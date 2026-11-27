//! Series 数值运算扩展：abs / round / clip / between / cumsum / cumprod / cummax / cummin / shift / where / mask。
//!
//! 设计原则：
//! - 仅在 Rust 层可高效加速的 dtype（Int64/Float64/Bool）上执行；
//!   Object/Categorical 列返回 None，由 Python 层回退到通用实现。
//! - 所有方法均保留原列名；返回 ``Option<Series>`` 的方法在 dtype 不支持
//!   或参数无法解析时返回 None，调用方回退到 Python。

use rayon::prelude::*;

use crate::core::dtype::ColumnData;
use crate::core::series::Series;

/// 将 f64 格式化为字符串，匹配 Python ``str(float)`` 的常见行为：
/// - NaN → "nan"
/// - +inf → "inf"，-inf → "-inf"
/// - 整数值的有限浮点数（如 2.0）→ "2.0"（Rust 默认 ``to_string`` 返回 "2"）
/// - 其他有限浮点数沿用 Rust 默认 ``to_string``
///
/// 注意：科学计数法的格式可能与 Python 略有差异（如 "1e100" vs "1e+100"），
/// 极端边界情况由 Python 层回退处理。
fn format_f64_like_python(val: f64) -> String {
    if val.is_nan() {
        return "nan".to_string();
    }
    if val.is_infinite() {
        return if val > 0.0 {
            "inf".to_string()
        } else {
            "-inf".to_string()
        };
    }
    let s = val.to_string();
    // 整数值的有限浮点数：Rust 给出 "2"，Python 给出 "2.0"
    if val.fract() == 0.0 && !s.contains('.') && !s.contains('e') && !s.contains('E') {
        format!("{s}.0")
    } else {
        s
    }
}

impl Series {
    // ---------- 绝对值 ----------

    /// 逐元素绝对值。
    ///
    /// - Int64/Float64：返回同 dtype Series。
    /// - Bool/String/Categorical：返回 None（Python 层回退）。
    pub fn abs(&self) -> Option<Series> {
        let data = match &self.data {
            ColumnData::Int(v) => {
                let result: Vec<Option<i64>> =
                    v.par_iter().map(|x| x.map(|val| val.abs())).collect();
                ColumnData::Int(result)
            }
            ColumnData::Float(v) => {
                let result: Vec<Option<f64>> =
                    v.par_iter().map(|x| x.map(|val| val.abs())).collect();
                ColumnData::Float(result)
            }
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    // ---------- 四舍五入 ----------

    /// 逐元素四舍五入到 ``decimals`` 位小数（仅 Float64 列）。
    /// Int64 列返回原 Series clone（无需处理）。
    /// 其他 dtype 返回 None。
    pub fn round(&self, decimals: i32) -> Option<Series> {
        let data = match &self.data {
            ColumnData::Int(_) => self.data.clone(),
            ColumnData::Float(v) => {
                let factor = 10f64.powi(decimals);
                let result: Vec<Option<f64>> = v
                    .par_iter()
                    .map(|x| x.map(|val| (val * factor).round() / factor))
                    .collect();
                ColumnData::Float(result)
            }
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    // ---------- 上下界裁剪 ----------

    /// 逐元素裁剪到 ``[lower, upper]`` 区间。
    /// - 仅 Int64/Float64 列加速；其他列返回 None。
    /// - lower/upper 任一为 None 表示该侧无限制。
    /// - NaN 视为缺失，保持原样（不参与裁剪）。
    pub fn clip(
        &self,
        lower: Option<f64>,
        upper: Option<f64>,
        lower_is_int: bool,
        upper_is_int: bool,
    ) -> Option<Series> {
        // 至少一侧必须有限
        if lower.is_none() && upper.is_none() {
            return Some(self.clone());
        }
        let lower_i = lower.map(|v| v as i64);
        let upper_i = upper.map(|v| v as i64);

        let data = match &self.data {
            ColumnData::Int(v) => {
                let result: Vec<Option<i64>> = v
                    .par_iter()
                    .map(|x| {
                        x.map(|val| {
                            let mut v = val;
                            if let Some(lo) = lower_i
                                && v < lo
                            {
                                v = lo;
                            }
                            if let Some(hi) = upper_i
                                && v > hi
                            {
                                v = hi;
                            }
                            v
                        })
                    })
                    .collect();
                ColumnData::Int(result)
            }
            ColumnData::Float(v) => {
                // 当 lower/upper 来自 int 字面量时，用精确整数值参与比较
                let lo_eff = if lower_is_int {
                    lower_i.map(|i| i as f64)
                } else {
                    lower
                };
                let hi_eff = if upper_is_int {
                    upper_i.map(|i| i as f64)
                } else {
                    upper
                };
                let result: Vec<Option<f64>> = v
                    .par_iter()
                    .map(|x| {
                        x.map(|val| {
                            let mut v = val;
                            if let Some(lo) = lo_eff
                                && v < lo
                            {
                                v = lo;
                            }
                            if let Some(hi) = hi_eff
                                && v > hi
                            {
                                v = hi;
                            }
                            v
                        })
                    })
                    .collect();
                ColumnData::Float(result)
            }
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    // ---------- 范围判断 ----------

    /// 逐元素判断是否在 ``[lower, upper]`` 区间（含端点）。
    /// - 仅 Int64/Float64 列加速；其他列返回 None。
    /// - 返回 Bool Series（None 位置保持 None）。
    /// - ``inclusive``：'both' / 'left' / 'right' / 'neither'。
    pub fn between(&self, lower: f64, upper: f64, inclusive: &str) -> Option<Series> {
        // 0 = both, 1 = left, 2 = right, 3 = neither
        let mode: u8 = match inclusive {
            "both" => 0,
            "left" => 1,
            "right" => 2,
            "neither" => 3,
            _ => 0,
        };
        // 内联判断，避免函数指针元组（clippy type_complexity 警告）
        let check = |v: f64| -> bool {
            match mode {
                0 => v >= lower && v <= upper,
                1 => v >= lower && v < upper,
                2 => v > lower && v <= upper,
                _ => v > lower && v < upper,
            }
        };

        let mask: Vec<Option<bool>> = match &self.data {
            ColumnData::Int(v) => v
                .par_iter()
                .map(|x| Some(x.map(|val| check(val as f64)).unwrap_or(false)))
                .collect(),
            ColumnData::Float(v) => v
                .par_iter()
                .map(|x| Some(x.map(&check).unwrap_or(false)))
                .collect(),
            _ => return None,
        };

        Some(Series {
            name: self.name.clone(),
            data: ColumnData::Bool(mask),
        })
    }

    // ---------- 累积运算 ----------

    /// 累积求和。仅 Int64/Float64 列加速；其他列返回 None。
    /// None 位置保持当前累积值不变（前导 None 返回 None，匹配 主流库 skipna=True 行为）。
    pub fn cumsum(&self) -> Option<Series> {
        let data = match &self.data {
            ColumnData::Int(v) => {
                let mut acc: Option<i64> = None;
                let result: Vec<Option<i64>> = v
                    .iter()
                    .map(|x| {
                        if let Some(val) = x {
                            acc = Some(match acc {
                                Some(a) => a.wrapping_add(*val),
                                None => *val,
                            });
                        }
                        acc
                    })
                    .collect();
                ColumnData::Int(result)
            }
            ColumnData::Float(v) => {
                let mut acc: Option<f64> = None;
                let result: Vec<Option<f64>> = v
                    .iter()
                    .map(|x| {
                        if let Some(val) = x {
                            acc = Some(match acc {
                                Some(a) => a + val,
                                None => *val,
                            });
                        }
                        acc
                    })
                    .collect();
                ColumnData::Float(result)
            }
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    /// 累积乘积。仅 Int64/Float64 列加速；其他列返回 None。
    /// None 位置保持当前累积值不变（前导 None 返回 None）。
    pub fn cumprod(&self) -> Option<Series> {
        let data = match &self.data {
            ColumnData::Int(v) => {
                let mut acc: Option<i64> = None;
                let result: Vec<Option<i64>> = v
                    .iter()
                    .map(|x| {
                        if let Some(val) = x {
                            acc = Some(match acc {
                                Some(a) => a.wrapping_mul(*val),
                                None => *val,
                            });
                        }
                        acc
                    })
                    .collect();
                ColumnData::Int(result)
            }
            ColumnData::Float(v) => {
                let mut acc: Option<f64> = None;
                let result: Vec<Option<f64>> = v
                    .iter()
                    .map(|x| {
                        if let Some(val) = x {
                            acc = Some(match acc {
                                Some(a) => a * val,
                                None => *val,
                            });
                        }
                        acc
                    })
                    .collect();
                ColumnData::Float(result)
            }
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    /// 累积最小值。仅 Int64/Float64 列加速；其他列返回 None。
    /// None 跳过（不影响累积值）。
    pub fn cummin(&self) -> Option<Series> {
        let data = match &self.data {
            ColumnData::Int(v) => {
                let mut acc: Option<i64> = None;
                let result: Vec<Option<i64>> = v
                    .iter()
                    .map(|x| {
                        if let Some(val) = x {
                            acc = Some(match acc {
                                Some(a) => a.min(*val),
                                None => *val,
                            });
                        }
                        acc
                    })
                    .collect();
                ColumnData::Int(result)
            }
            ColumnData::Float(v) => {
                let mut acc: Option<f64> = None;
                let result: Vec<Option<f64>> = v
                    .iter()
                    .map(|x| {
                        if let Some(val) = x {
                            acc = Some(match acc {
                                Some(a) => a.min(*val),
                                None => *val,
                            });
                        }
                        acc
                    })
                    .collect();
                ColumnData::Float(result)
            }
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    /// 累积最大值。仅 Int64/Float64 列加速；其他列返回 None。
    /// None 跳过（不影响累积值）。
    pub fn cummax(&self) -> Option<Series> {
        let data = match &self.data {
            ColumnData::Int(v) => {
                let mut acc: Option<i64> = None;
                let result: Vec<Option<i64>> = v
                    .iter()
                    .map(|x| {
                        if let Some(val) = x {
                            acc = Some(match acc {
                                Some(a) => a.max(*val),
                                None => *val,
                            });
                        }
                        acc
                    })
                    .collect();
                ColumnData::Int(result)
            }
            ColumnData::Float(v) => {
                let mut acc: Option<f64> = None;
                let result: Vec<Option<f64>> = v
                    .iter()
                    .map(|x| {
                        if let Some(val) = x {
                            acc = Some(match acc {
                                Some(a) => a.max(*val),
                                None => *val,
                            });
                        }
                        acc
                    })
                    .collect();
                ColumnData::Float(result)
            }
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    // ---------- 重复 ----------

    /// 各元素按指定次数重复 (pandas repeat 语义)。
    /// 调用方需保证 repeats.len() 与列长一致。
    pub fn repeat(&self, repeats: &[usize]) -> Series {
        Series {
            name: self.name.clone(),
            data: self.data.repeat(repeats),
        }
    }

    // ---------- 偏移 ----------

    /// 按 ``periods`` 偏移数据：正数向下偏移（前面补 None），
    /// 负数向上偏移（后面补 None）。``periods == 0`` 返回 clone。
    /// 仅 Int64/Float64/Bool/String 列加速；Categorical 返回 None。
    pub fn shift(&self, periods: i32) -> Option<Series> {
        let n = self.len();
        if n == 0 || periods == 0 {
            return Some(self.clone());
        }
        let p = periods.unsigned_abs() as usize;
        if p >= n {
            // 全部填充 None
            return Some(Series::new_null(self.name.clone(), self.dtype(), n));
        }

        let data = match &self.data {
            ColumnData::Int(v) => {
                let result: Vec<Option<i64>> = if periods > 0 {
                    let mut r = vec![None; p];
                    r.extend(v.iter().take(n - p).copied());
                    r
                } else {
                    let mut r: Vec<Option<i64>> = v.iter().skip(p).copied().collect();
                    r.extend(std::iter::repeat_n(None, p));
                    r
                };
                ColumnData::Int(result)
            }
            ColumnData::Float(v) => {
                let result: Vec<Option<f64>> = if periods > 0 {
                    let mut r = vec![None; p];
                    r.extend(v.iter().take(n - p).copied());
                    r
                } else {
                    let mut r: Vec<Option<f64>> = v.iter().skip(p).copied().collect();
                    r.extend(std::iter::repeat_n(None, p));
                    r
                };
                ColumnData::Float(result)
            }
            ColumnData::Bool(v) => {
                let result: Vec<Option<bool>> = if periods > 0 {
                    let mut r = vec![None; p];
                    r.extend(v.iter().take(n - p).copied());
                    r
                } else {
                    let mut r: Vec<Option<bool>> = v.iter().skip(p).copied().collect();
                    r.extend(std::iter::repeat_n(None, p));
                    r
                };
                ColumnData::Bool(result)
            }
            ColumnData::String(v) => {
                let result: Vec<Option<String>> = if periods > 0 {
                    let mut r = vec![None; p];
                    r.extend(v.iter().take(n - p).cloned());
                    r
                } else {
                    let mut r: Vec<Option<String>> = v.iter().skip(p).cloned().collect();
                    r.extend(std::iter::repeat_n(None, p));
                    r
                };
                ColumnData::String(result)
            }
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    // ---------- 条件选择 ----------

    /// 三元条件选择：``cond[i]`` 为 true 取 ``self[i]``，否则取 ``other[i]``。
    /// - 仅同 dtype 同长度的 Int64/Float64/Bool/String 列加速；其他返回 None。
    /// - ``other`` 长度不同或 dtype 不匹配 → 返回 None。
    /// - ``cond`` 长度不同 → 返回 None。
    pub fn where_cond(&self, cond: &[bool], other: &Series) -> Option<Series> {
        if cond.len() != self.len() || other.len() != self.len() {
            return None;
        }
        if self.dtype() != other.dtype() {
            return None;
        }
        let n = self.len();
        let data = match (&self.data, &other.data) {
            (ColumnData::Int(a), ColumnData::Int(b)) => {
                let result: Vec<Option<i64>> = (0..n)
                    .into_par_iter()
                    .map(|i| if cond[i] { a[i] } else { b[i] })
                    .collect();
                ColumnData::Int(result)
            }
            (ColumnData::Float(a), ColumnData::Float(b)) => {
                let result: Vec<Option<f64>> = (0..n)
                    .into_par_iter()
                    .map(|i| if cond[i] { a[i] } else { b[i] })
                    .collect();
                ColumnData::Float(result)
            }
            (ColumnData::Bool(a), ColumnData::Bool(b)) => {
                let result: Vec<Option<bool>> = (0..n)
                    .into_par_iter()
                    .map(|i| if cond[i] { a[i] } else { b[i] })
                    .collect();
                ColumnData::Bool(result)
            }
            (ColumnData::String(a), ColumnData::String(b)) => {
                let result: Vec<Option<String>> = (0..n)
                    .into_par_iter()
                    .map(|i| if cond[i] { a[i].clone() } else { b[i].clone() })
                    .collect();
                ColumnData::String(result)
            }
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    /// 百分比变化：``(x[i] - x[i-periods]) / x[i-periods]``。
    /// - 仅 Int64/Float64 列加速；其他列返回 None。
    /// - 跳过 None 与 NaN：原值或前值任一缺失时结果为 None。
    /// - 前值为 0 时结果为 None（避免除零）。
    /// - ``periods == 0`` 返回全 0.0 的 Float64 Series（与 主流库 一致）。
    /// - ``abs(periods) >= n`` 返回全 None 的 Series。
    ///
    /// 结果恒为 Float64 列（与 主流库 pct_change 一致）。
    pub fn pct_change(&self, periods: i32) -> Option<Series> {
        let n = self.len();
        if n == 0 {
            return Some(self.clone());
        }
        let p = periods;
        if p == 0 {
            // 与 主流库 一致：返回全 0
            let data = match &self.data {
                ColumnData::Int(v) => {
                    let result: Vec<Option<f64>> = v.par_iter().map(|x| x.map(|_| 0.0)).collect();
                    ColumnData::Float(result)
                }
                ColumnData::Float(v) => {
                    let result: Vec<Option<f64>> = v.par_iter().map(|x| x.map(|_| 0.0)).collect();
                    ColumnData::Float(result)
                }
                _ => return None,
            };
            return Some(Series {
                name: self.name.clone(),
                data,
            });
        }
        let abs_p = p.unsigned_abs() as usize;
        if abs_p >= n {
            // 全 None
            let data = match &self.data {
                ColumnData::Int(_) => ColumnData::Float(vec![None; n]),
                ColumnData::Float(_) => ColumnData::Float(vec![None; n]),
                _ => return None,
            };
            return Some(Series {
                name: self.name.clone(),
                data,
            });
        }
        let data = match &self.data {
            ColumnData::Int(v) => {
                let result: Vec<Option<f64>> = if p > 0 {
                    let head = vec![None; abs_p];
                    let tail: Vec<Option<f64>> = (abs_p..n)
                        .into_par_iter()
                        .map(|i| {
                            let cur = v[i]?;
                            let prev = v[i - abs_p]?;
                            if prev == 0 {
                                None
                            } else {
                                Some((cur as f64 - prev as f64) / prev as f64)
                            }
                        })
                        .collect();
                    head.into_iter().chain(tail).collect()
                } else {
                    let tail_pad = vec![None; abs_p];
                    let head: Vec<Option<f64>> = (0..n - abs_p)
                        .into_par_iter()
                        .map(|i| {
                            let cur = v[i]?;
                            let prev = v[i + abs_p]?;
                            if prev == 0 {
                                None
                            } else {
                                Some((cur as f64 - prev as f64) / prev as f64)
                            }
                        })
                        .collect();
                    head.into_iter().chain(tail_pad).collect()
                };
                ColumnData::Float(result)
            }
            ColumnData::Float(v) => {
                let result: Vec<Option<f64>> = if p > 0 {
                    let head = vec![None; abs_p];
                    let tail: Vec<Option<f64>> = (abs_p..n)
                        .into_par_iter()
                        .map(|i| {
                            let cur = v[i]?;
                            let prev = v[i - abs_p]?;
                            if prev.is_nan() || prev == 0.0 {
                                None
                            } else {
                                Some((cur - prev) / prev)
                            }
                        })
                        .collect();
                    head.into_iter().chain(tail).collect()
                } else {
                    let tail_pad = vec![None; abs_p];
                    let head: Vec<Option<f64>> = (0..n - abs_p)
                        .into_par_iter()
                        .map(|i| {
                            let cur = v[i]?;
                            let prev = v[i + abs_p]?;
                            if prev.is_nan() || prev == 0.0 {
                                None
                            } else {
                                Some((cur - prev) / prev)
                            }
                        })
                        .collect();
                    head.into_iter().chain(tail_pad).collect()
                };
                ColumnData::Float(result)
            }
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    // ---------- 点积 (dot) ----------

    /// 计算点积：``sum(self[i] * other[i])``，跳过任一侧为 None / NaN 的位置。
    ///
    /// - 仅 Int64/Float64/Bool 列加速；String/Categorical 列返回 None。
    /// - 长度不匹配返回 None（由 Python 层抛 ValueError）。
    /// - 返回 :enum:`AggResult::Float`（统一为 f64，与 Python ``sum`` 语义一致）。
    pub fn dot_f64(&self, other: &[Option<f64>]) -> Option<f64> {
        if self.len() != other.len() {
            return None;
        }
        let n = self.len();
        if n == 0 {
            return Some(0.0);
        }
        let result = match &self.data {
            ColumnData::Int(v) => (0..n)
                .into_par_iter()
                .map(|i| match (v[i], other[i]) {
                    (Some(x), Some(y)) => x as f64 * y,
                    _ => 0.0,
                })
                .sum(),
            ColumnData::Float(v) => (0..n)
                .into_par_iter()
                .map(|i| match (v[i], other[i]) {
                    (Some(x), Some(y)) if !x.is_nan() && !y.is_nan() => x * y,
                    _ => 0.0,
                })
                .sum(),
            ColumnData::Bool(v) => (0..n)
                .into_par_iter()
                .map(|i| match (v[i], other[i]) {
                    (Some(x), Some(y)) => (if x { 1.0 } else { 0.0 }) * y,
                    _ => 0.0,
                })
                .sum(),
            _ => return None,
        };
        Some(result)
    }

    // ---------- 类型转换 (astype) ----------

    /// 通用类型转换：将当前 Series 转换为 ``target`` dtype。
    ///
    /// 支持的目标族：
    /// - ``int`` / ``int8``..``uint64``：统一存储为 Int64（Rust 层不区分子类型，
    ///   Python 层通过 ``_dtype_str`` 追踪精确子类型）。
    /// - ``float`` / ``float32`` / ``float64``：统一存储为 Float64。
    /// - ``bool``：0/0.0/"false" → false，非零 → true，解析失败 → None。
    /// - ``object`` / ``str`` / ``string``：调用 ``to_string`` 转为字符串列。
    ///
    /// 不支持的场景（返回 None，由 Python 回退）：
    /// - 源列为 Categorical（Python 层处理 categories/codes）。
    /// - 目标为 ``category`` / ``datetime64`` 等特殊 dtype。
    /// - 未知 target 字符串。
    pub fn astype(&self, target: &str) -> Option<Series> {
        let target_lower = target.to_ascii_lowercase();
        let is_int_family = |t: &str| t == "int" || t.starts_with("int") || t.starts_with("uint");
        let is_float_family = |t: &str| t == "float" || t.starts_with("float");
        let is_str_family = |t: &str| t == "object" || t == "str" || t == "string";

        let data = match (&self.data, target_lower.as_str()) {
            // ---------- 同族 / 同 dtype ----------
            (ColumnData::Int(_), t) if is_int_family(t) => self.data.clone(),
            (ColumnData::Float(_), t) if is_float_family(t) => self.data.clone(),
            (ColumnData::Bool(_), "bool") => self.data.clone(),
            (ColumnData::String(_), t) if is_str_family(t) => self.data.clone(),

            // ---------- -> int 族 ----------
            (ColumnData::Float(v), t) if is_int_family(t) => {
                let result: Vec<Option<i64>> = v
                    .par_iter()
                    .map(|x| {
                        x.and_then(|val| {
                            if val.is_nan() || val.is_infinite() {
                                None
                            } else {
                                Some(val as i64)
                            }
                        })
                    })
                    .collect();
                ColumnData::Int(result)
            }
            (ColumnData::Bool(v), t) if is_int_family(t) => {
                let result: Vec<Option<i64>> = v.par_iter().map(|x| x.map(|b| b as i64)).collect();
                ColumnData::Int(result)
            }
            (ColumnData::String(v), t) if is_int_family(t) => {
                let result: Vec<Option<i64>> = v
                    .par_iter()
                    .map(|x| x.as_ref().and_then(|s| s.trim().parse::<i64>().ok()))
                    .collect();
                ColumnData::Int(result)
            }

            // ---------- -> float 族 ----------
            (ColumnData::Int(v), t) if is_float_family(t) => {
                let result: Vec<Option<f64>> =
                    v.par_iter().map(|x| x.map(|val| val as f64)).collect();
                ColumnData::Float(result)
            }
            (ColumnData::Bool(v), t) if is_float_family(t) => {
                let result: Vec<Option<f64>> = v
                    .par_iter()
                    .map(|x| x.map(|b| if b { 1.0 } else { 0.0 }))
                    .collect();
                ColumnData::Float(result)
            }
            (ColumnData::String(v), t) if is_float_family(t) => {
                let result: Vec<Option<f64>> = v
                    .par_iter()
                    .map(|x| x.as_ref().and_then(|s| s.trim().parse::<f64>().ok()))
                    .collect();
                ColumnData::Float(result)
            }

            // ---------- -> bool ----------
            (ColumnData::Int(v), "bool") => {
                let result: Vec<Option<bool>> =
                    v.par_iter().map(|x| x.map(|val| val != 0)).collect();
                ColumnData::Bool(result)
            }
            (ColumnData::Float(v), "bool") => {
                let result: Vec<Option<bool>> =
                    v.par_iter().map(|x| x.map(|val| val != 0.0)).collect();
                ColumnData::Bool(result)
            }
            (ColumnData::String(v), "bool") => {
                let result: Vec<Option<bool>> = v
                    .par_iter()
                    .map(|x| {
                        x.as_ref().and_then(|s| {
                            let lower = s.to_ascii_lowercase();
                            match lower.as_str() {
                                "true" | "1" => Some(true),
                                "false" | "0" => Some(false),
                                _ => None,
                            }
                        })
                    })
                    .collect();
                ColumnData::Bool(result)
            }

            // ---------- -> str / object ----------
            (ColumnData::Int(v), t) if is_str_family(t) => {
                let result: Vec<Option<String>> =
                    v.par_iter().map(|x| x.map(|val| val.to_string())).collect();
                ColumnData::String(result)
            }
            (ColumnData::Float(v), t) if is_str_family(t) => {
                let result: Vec<Option<String>> = v
                    .par_iter()
                    .map(|x| x.map(format_f64_like_python))
                    .collect();
                ColumnData::String(result)
            }
            (ColumnData::Bool(v), t) if is_str_family(t) => {
                let result: Vec<Option<String>> =
                    v.par_iter().map(|x| x.map(|b| b.to_string())).collect();
                ColumnData::String(result)
            }

            // ---------- 不支持 ----------
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::dtype::DType;

    #[test]
    fn test_abs() {
        let s = Series::new_int(None, vec![Some(-3), Some(2), Some(-1), None]);
        let r = s.abs().expect("abs 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![Some(3), Some(2), Some(1), None]);
        } else {
            panic!("dtype 错误");
        }

        let sf = Series::new_float(None, vec![Some(-1.5), Some(2.0), None]);
        let rf = sf.abs().expect("abs float 应成功");
        if let ColumnData::Float(v) = &rf.data {
            assert_eq!(v[0], Some(1.5));
            assert_eq!(v[1], Some(2.0));
            assert_eq!(v[2], None);
        }
    }

    #[test]
    fn test_round() {
        let s = Series::new_float(None, vec![Some(1.234), Some(2.345), Some(3.456)]);
        let r = s.round(2).expect("round 应成功");
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v[0], Some(1.23));
            assert_eq!(v[1], Some(2.35));
            assert_eq!(v[2], Some(3.46));
        }

        // Int 列原样返回
        let si = Series::new_int(None, vec![Some(1), Some(2)]);
        let ri = si.round(2).expect("round int 应返回 clone");
        assert_eq!(ri.len(), 2);
    }

    #[test]
    fn test_clip() {
        let s = Series::new_int(None, vec![Some(-5), Some(0), Some(5), Some(10)]);
        let r = s
            .clip(Some(0.0), Some(7.0), true, true)
            .expect("clip 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![Some(0), Some(0), Some(5), Some(7)]);
        }

        let sf = Series::new_float(None, vec![Some(-1.5), Some(0.5), Some(2.5)]);
        let rf = sf
            .clip(Some(0.0), Some(2.0), false, false)
            .expect("clip float 应成功");
        if let ColumnData::Float(v) = &rf.data {
            assert_eq!(v[0], Some(0.0));
            assert_eq!(v[1], Some(0.5));
            assert_eq!(v[2], Some(2.0));
        }
    }

    #[test]
    fn test_between() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(3), Some(4)]);
        let r = s.between(2.0, 4.0, "both").expect("between 应成功");
        assert_eq!(r.dtype(), DType::Bool);
        if let ColumnData::Bool(v) = &r.data {
            assert_eq!(v, &vec![Some(false), Some(true), Some(true), Some(true)]);
        }

        let r2 = s
            .between(2.0, 4.0, "neither")
            .expect("between neither 应成功");
        if let ColumnData::Bool(v) = &r2.data {
            assert_eq!(v, &vec![Some(false), Some(false), Some(true), Some(false)]);
        }
    }

    #[test]
    fn test_cumsum() {
        let s = Series::new_int(None, vec![Some(1), Some(2), None, Some(4)]);
        let r = s.cumsum().expect("cumsum 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![Some(1), Some(3), Some(3), Some(7)]);
        }
    }

    #[test]
    fn test_cumsum_leading_none() {
        // 前导 None：保持 None（匹配 主流库 skipna=True）
        let s = Series::new_int(None, vec![None, Some(1), Some(2), None, Some(4)]);
        let r = s.cumsum().expect("cumsum 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![None, Some(1), Some(3), Some(3), Some(7)]);
        }
    }

    #[test]
    fn test_cumprod_leading_none() {
        let s = Series::new_int(None, vec![None, Some(2), Some(3)]);
        let r = s.cumprod().expect("cumprod 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![None, Some(2), Some(6)]);
        }
    }

    #[test]
    fn test_cumprod() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(3)]);
        let r = s.cumprod().expect("cumprod 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![Some(1), Some(2), Some(6)]);
        }
    }

    #[test]
    fn test_cummin() {
        let s = Series::new_int(None, vec![Some(5), Some(3), None, Some(8), Some(2)]);
        let r = s.cummin().expect("cummin 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![Some(5), Some(3), Some(3), Some(3), Some(2)]);
        }
    }

    #[test]
    fn test_cummax() {
        let s = Series::new_int(None, vec![Some(1), Some(5), Some(3), Some(7)]);
        let r = s.cummax().expect("cummax 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![Some(1), Some(5), Some(5), Some(7)]);
        }
    }

    #[test]
    fn test_shift_positive() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(3), Some(4)]);
        let r = s.shift(1).expect("shift 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![None, Some(1), Some(2), Some(3)]);
        }
    }

    #[test]
    fn test_shift_negative() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(3), Some(4)]);
        let r = s.shift(-1).expect("shift -1 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![Some(2), Some(3), Some(4), None]);
        }
    }

    #[test]
    fn test_shift_zero() {
        let s = Series::new_int(None, vec![Some(1), Some(2)]);
        let r = s.shift(0).expect("shift 0 应返回 clone");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![Some(1), Some(2)]);
        }
    }

    #[test]
    fn test_shift_exceeds_len() {
        let s = Series::new_int(None, vec![Some(1), Some(2)]);
        let r = s.shift(5).expect("shift 5 应返回全 None");
        assert_eq!(r.len(), 2);
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], None);
            assert_eq!(v[1], None);
        }
    }

    #[test]
    fn test_where_cond() {
        let a = Series::new_int(None, vec![Some(1), Some(2), Some(3)]);
        let b = Series::new_int(None, vec![Some(10), Some(20), Some(30)]);
        let cond = vec![true, false, true];
        let r = a.where_cond(&cond, &b).expect("where 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![Some(1), Some(20), Some(3)]);
        }
    }

    #[test]
    fn test_where_dtype_mismatch() {
        let a = Series::new_int(None, vec![Some(1)]);
        let b = Series::new_float(None, vec![Some(1.0)]);
        let cond = vec![true];
        assert!(a.where_cond(&cond, &b).is_none());
    }

    #[test]
    fn test_abs_unsupported_dtype() {
        let s = Series::new_bool(None, vec![Some(true), Some(false)]);
        assert!(s.abs().is_none());
    }

    // ---------- astype 测试 ----------

    #[test]
    fn test_astype_int_to_float() {
        let s = Series::new_int(None, vec![Some(1), Some(2), None, Some(4)]);
        let r = s.astype("float64").expect("astype float 应成功");
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v[0], Some(1.0));
            assert_eq!(v[1], Some(2.0));
            assert_eq!(v[2], None);
            assert_eq!(v[3], Some(4.0));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_astype_float_to_int() {
        let s = Series::new_float(None, vec![Some(1.5), Some(2.0), Some(f64::NAN), None]);
        let r = s.astype("int64").expect("astype int 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], Some(1)); // 截断
            assert_eq!(v[1], Some(2));
            assert_eq!(v[2], None); // NaN → None
            assert_eq!(v[3], None);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_astype_int_to_bool() {
        let s = Series::new_int(None, vec![Some(0), Some(1), Some(5), None]);
        let r = s.astype("bool").expect("astype bool 应成功");
        if let ColumnData::Bool(v) = &r.data {
            assert_eq!(v[0], Some(false));
            assert_eq!(v[1], Some(true));
            assert_eq!(v[2], Some(true));
            assert_eq!(v[3], None);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_astype_string_to_int() {
        let s = Series::new_string(
            None,
            vec![
                Some("1".into()),
                Some("  42 ".into()),
                Some("x".into()),
                None,
            ],
        );
        let r = s.astype("int64").expect("astype int 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], Some(1));
            assert_eq!(v[1], Some(42));
            assert_eq!(v[2], None); // 解析失败
            assert_eq!(v[3], None);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_astype_string_to_bool() {
        let s = Series::new_string(
            None,
            vec![
                Some("true".into()),
                Some("FALSE".into()),
                Some("1".into()),
                Some("xxx".into()),
            ],
        );
        let r = s.astype("bool").expect("astype bool 应成功");
        if let ColumnData::Bool(v) = &r.data {
            assert_eq!(v[0], Some(true));
            assert_eq!(v[1], Some(false));
            assert_eq!(v[2], Some(true));
            assert_eq!(v[3], None); // 未知字符串 → None
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_astype_int_to_string() {
        let s = Series::new_int(None, vec![Some(1), Some(2), None]);
        let r = s.astype("object").expect("astype object 应成功");
        if let ColumnData::String(v) = &r.data {
            assert_eq!(v[0], Some("1".into()));
            assert_eq!(v[1], Some("2".into()));
            assert_eq!(v[2], None);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_astype_same_family_clone() {
        let s = Series::new_int(None, vec![Some(1), Some(2)]);
        let r = s.astype("int32").expect("astype int32 应返回 clone");
        assert_eq!(r.len(), 2);
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], Some(1));
            assert_eq!(v[1], Some(2));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_astype_unknown_target_returns_none() {
        let s = Series::new_int(None, vec![Some(1)]);
        assert!(s.astype("category").is_none());
        assert!(s.astype("datetime64[ns]").is_none());
    }

    // ---------- pct_change 测试 ----------

    #[test]
    fn test_pct_change_int_positive() {
        let s = Series::new_int(None, vec![Some(100), Some(110), Some(121)]);
        let r = s.pct_change(1).expect("pct_change 应成功");
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v[0], None);
            assert!((v[1].unwrap() - 0.10).abs() < 1e-9);
            assert!((v[2].unwrap() - 0.10).abs() < 1e-9);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_pct_change_float_negative_period() {
        let s = Series::new_float(None, vec![Some(1.0), Some(2.0), Some(3.0)]);
        let r = s.pct_change(-1).expect("pct_change -1 应成功");
        if let ColumnData::Float(v) = &r.data {
            assert!((v[0].unwrap() - 1.0).abs() < 1e-9);
            assert!((v[1].unwrap() - 0.5).abs() < 1e-9);
            assert_eq!(v[2], None);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_pct_change_zero_prev_returns_none() {
        let s = Series::new_int(None, vec![Some(0), Some(5)]);
        let r = s.pct_change(1).expect("pct_change 应成功");
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v[0], None);
            assert_eq!(v[1], None); // 前值为 0 → None
        }
    }

    #[test]
    fn test_pct_change_periods_zero() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(3)]);
        let r = s.pct_change(0).expect("pct_change 0 应成功");
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v, &vec![Some(0.0), Some(0.0), Some(0.0)]);
        }
    }

    #[test]
    fn test_pct_change_exceeds_len() {
        let s = Series::new_int(None, vec![Some(1), Some(2)]);
        let r = s.pct_change(5).expect("pct_change 越界应返回全 None");
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v[0], None);
            assert_eq!(v[1], None);
        }
    }

    #[test]
    fn test_pct_change_with_none() {
        let s = Series::new_int(None, vec![Some(10), None, Some(20)]);
        let r = s.pct_change(1).expect("pct_change 应成功");
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v[0], None);
            assert_eq!(v[1], None); // 当前值为 None
            assert_eq!(v[2], None); // 前值为 None
        }
    }

    #[test]
    fn test_pct_change_unsupported_dtype() {
        let s = Series::new_bool(None, vec![Some(true), Some(false)]);
        assert!(s.pct_change(1).is_none());
    }
}
