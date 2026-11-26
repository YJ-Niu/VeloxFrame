//! Series 扩展运算：replace / diff / drop_duplicates / combine_first。
//!
//! 本模块提供 5 个加速方法，覆盖 pandas.Series 中常用的替换、差分、去重、
//! 缺失值合并等场景。设计原则：
//! - 仅在 Rust 层可加速的 dtype 上执行（Int64/Float64/Bool/Categorical），
//!   Object 列（即 :class:`ColumnData::String`）统一返回 None，由 Python 层回退。
//! - 凡返回 :struct:`Series` 的方法保留原列名；凡返回 :struct:`Option<Series>`
//!   的方法在 dtype 不支持、长度不匹配、解析失败时返回 None，Python 层回退到
//!   通用实现，避免在 Rust 层抛异常破坏调用方语义。

use std::collections::{HashMap, HashSet};

use rayon::prelude::*;

use crate::core::dtype::{CategoricalData, ColumnData};
use crate::core::series::Series;

impl Series {
    // ---------- 标量替换 ----------

    /// 标量值替换：将 ``old_str`` 表示的值替换为 ``new_str`` 表示的值。
    ///
    /// Python 层会把任意 Python 对象先转为字符串再传入，因此 ``old_str`` / ``new_str``
    /// 均为字符串。本方法根据 self 的 dtype 选择合适的解析策略：
    ///
    /// - :enum:`ColumnData::Int`：将 ``old_str`` / ``new_str`` parse 为 i64 后逐元素替换；
    ///   parse 失败时返回 None（Python 层回退，因为可能传入的是浮点字面量）。
    /// - :enum:`ColumnData::Float`：将 ``old_str`` / ``new_str`` parse 为 f64 后逐元素替换；
    ///   parse 失败时返回 None。
    /// - :enum:`ColumnData::Bool`：将 ``old_str`` / ``new_str`` parse 为 bool（"true"/"false"，
    ///   大小写不敏感）后逐元素替换；parse 失败时返回 None。
    /// - :enum:`ColumnData::Categorical`：在 categories 列表上做字符串替换，受影响的
    ///   codes 自动指向新名称；不会失败。
    /// - :enum:`ColumnData::String`（即 Object 列）：返回 None，由 Python 层回退到
    ///   通用 replace 实现（Python 层 str.replace 已足够高效，且能处理混合类型）。
    pub fn replace_scalar(&self, old_str: &str, new_str: &str) -> Option<Series> {
        let data = match &self.data {
            ColumnData::Int(v) => {
                let old_val = old_str.parse::<i64>().ok()?;
                let new_val = new_str.parse::<i64>().ok()?;
                let result: Vec<Option<i64>> = v
                    .par_iter()
                    .map(|x| match x {
                        Some(val) if *val == old_val => Some(new_val),
                        _ => *x,
                    })
                    .collect();
                ColumnData::Int(result)
            }
            ColumnData::Float(v) => {
                let old_val = old_str.parse::<f64>().ok()?;
                let new_val = new_str.parse::<f64>().ok()?;
                // 用 to_bits 比较，确保 -0.0 与 +0.0、NaN 与 NaN 语义一致
                let old_bits = old_val.to_bits();
                let result: Vec<Option<f64>> = v
                    .par_iter()
                    .map(|x| match x {
                        Some(val) if val.to_bits() == old_bits => Some(new_val),
                        _ => *x,
                    })
                    .collect();
                ColumnData::Float(result)
            }
            ColumnData::Bool(v) => {
                let old_val = parse_bool_str(old_str)?;
                let new_val = parse_bool_str(new_str)?;
                let result: Vec<Option<bool>> = v
                    .par_iter()
                    .map(|x| match x {
                        Some(val) if *val == old_val => Some(new_val),
                        _ => *x,
                    })
                    .collect();
                ColumnData::Bool(result)
            }
            ColumnData::Categorical(c) => {
                // 在 categories 上做字符串替换：所有等于 old_str 的分类项统一改名为 new_str
                let new_categories: Vec<String> = c
                    .categories
                    .par_iter()
                    .map(|cat| {
                        if cat == old_str {
                            new_str.to_string()
                        } else {
                            cat.clone()
                        }
                    })
                    .collect();
                ColumnData::Categorical(CategoricalData {
                    categories: new_categories,
                    codes: c.codes.clone(),
                    ordered: c.ordered,
                })
            }
            // Object 列（ColumnData::String）：Rust 层不加速，返回 None 让 Python 回退
            ColumnData::String(_) => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    // ---------- 字典批量替换 ----------

    /// 字典批量替换：``pairs`` 是 ``(old_str, new_str)`` 列表。
    ///
    /// 与 :meth:`replace_scalar` 类似，根据 dtype 选择解析策略：
    ///
    /// - Int64/Float64/Bool：将所有 ``old_str`` / ``new_str`` 解析为目标类型并构建
    ///   :struct:`HashMap`，单次遍历完成替换。任一 pair 解析失败即返回 None。
    /// - Categorical：在 categories 列表上做字符串批量替换。
    /// - Object（ColumnData::String）：返回 None。
    pub fn replace_dict(&self, pairs: &[(String, String)]) -> Option<Series> {
        let data = match &self.data {
            ColumnData::Int(v) => {
                let mut map: HashMap<i64, i64> = HashMap::with_capacity(pairs.len());
                for (old_s, new_s) in pairs {
                    let old_v = old_s.parse::<i64>().ok()?;
                    let new_v = new_s.parse::<i64>().ok()?;
                    map.insert(old_v, new_v);
                }
                let result: Vec<Option<i64>> = v
                    .par_iter()
                    .map(|x| match x {
                        Some(val) => match map.get(val) {
                            Some(new_val) => Some(*new_val),
                            None => Some(*val),
                        },
                        None => None,
                    })
                    .collect();
                ColumnData::Int(result)
            }
            ColumnData::Float(v) => {
                let mut map: HashMap<u64, f64> = HashMap::with_capacity(pairs.len());
                for (old_s, new_s) in pairs {
                    let old_v = old_s.parse::<f64>().ok()?;
                    let new_v = new_s.parse::<f64>().ok()?;
                    map.insert(old_v.to_bits(), new_v);
                }
                let result: Vec<Option<f64>> = v
                    .par_iter()
                    .map(|x| match x {
                        Some(val) => match map.get(&val.to_bits()) {
                            Some(new_val) => Some(*new_val),
                            None => Some(*val),
                        },
                        None => None,
                    })
                    .collect();
                ColumnData::Float(result)
            }
            ColumnData::Bool(v) => {
                let mut map: HashMap<bool, bool> = HashMap::with_capacity(pairs.len());
                for (old_s, new_s) in pairs {
                    let old_v = parse_bool_str(old_s)?;
                    let new_v = parse_bool_str(new_s)?;
                    map.insert(old_v, new_v);
                }
                let result: Vec<Option<bool>> = v
                    .par_iter()
                    .map(|x| match x {
                        Some(val) => match map.get(val) {
                            Some(new_val) => Some(*new_val),
                            None => Some(*val),
                        },
                        None => None,
                    })
                    .collect();
                ColumnData::Bool(result)
            }
            ColumnData::Categorical(c) => {
                // 构建 old -> new 字符串映射，对 categories 批量改名
                let mut map: HashMap<String, String> = HashMap::with_capacity(pairs.len());
                for (old_s, new_s) in pairs {
                    map.insert(old_s.clone(), new_s.clone());
                }
                let new_categories: Vec<String> = c
                    .categories
                    .par_iter()
                    .map(|cat| match map.get(cat) {
                        Some(new_val) => new_val.clone(),
                        None => cat.clone(),
                    })
                    .collect();
                ColumnData::Categorical(CategoricalData {
                    categories: new_categories,
                    codes: c.codes.clone(),
                    ordered: c.ordered,
                })
            }
            // Object 列：返回 None 让 Python 回退
            ColumnData::String(_) => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    // ---------- 差分 ----------

    /// 计算差分：``result[i] = self[i] - self[i - periods]``。
    ///
    /// - ``periods > 0``：前 ``periods`` 个位置为 None（与 pandas 一致）。
    /// - ``periods < 0``：后 ``|periods|`` 个位置为 None。
    /// - ``periods == 0``：返回与 self 完全相同的 Series。
    /// - Int64/Float64 列：逐元素相减，None 传播（任一侧缺失则结果为 None）。
    /// - 其他列（Bool/String/Categorical）：返回全 None 的同 dtype Series，
    ///   Python 层会在该结果上做 datetime/timedelta 等后续处理。
    ///
    /// 注意：``periods`` 绝对值大于等于 ``len`` 时，结果为全 None（合法边界情况）。
    pub fn diff(&self, periods: i32) -> Series {
        let n = self.len();
        // periods == 0：直接返回 clone（避免无谓计算）
        if periods == 0 || n == 0 {
            return self.clone();
        }
        let p = periods.unsigned_abs() as usize;
        // |periods| >= n：结果必然全 None
        if p >= n {
            return Series::new_null(self.name.clone(), self.dtype(), n);
        }

        let data = match &self.data {
            ColumnData::Int(v) => {
                // 使用 map().collect() 模式，避免 for_each 闭包内可变借用 result
                let result: Vec<Option<i64>> = if periods > 0 {
                    // result[i] = v[i] - v[i - p]，前 p 个为 None
                    (0..n)
                        .into_par_iter()
                        .map(|i| {
                            if i < p {
                                None
                            } else {
                                match (v[i], v[i - p]) {
                                    (Some(a), Some(b)) => Some(a - b),
                                    _ => None,
                                }
                            }
                        })
                        .collect()
                } else {
                    // periods < 0：result[i] = v[i] - v[i + p]，后 p 个为 None
                    (0..n)
                        .into_par_iter()
                        .map(|i| {
                            if i >= n - p {
                                None
                            } else {
                                match (v[i], v[i + p]) {
                                    (Some(a), Some(b)) => Some(a - b),
                                    _ => None,
                                }
                            }
                        })
                        .collect()
                };
                ColumnData::Int(result)
            }
            ColumnData::Float(v) => {
                let result: Vec<Option<f64>> = if periods > 0 {
                    (0..n)
                        .into_par_iter()
                        .map(|i| {
                            if i < p {
                                None
                            } else {
                                match (v[i], v[i - p]) {
                                    (Some(a), Some(b)) => Some(a - b),
                                    _ => None,
                                }
                            }
                        })
                        .collect()
                } else {
                    (0..n)
                        .into_par_iter()
                        .map(|i| {
                            if i >= n - p {
                                None
                            } else {
                                match (v[i], v[i + p]) {
                                    (Some(a), Some(b)) => Some(a - b),
                                    _ => None,
                                }
                            }
                        })
                        .collect()
                };
                ColumnData::Float(result)
            }
            // 其他类型：返回全 None 的同 dtype Series（Python 层处理 datetime 等）
            _ => return Series::new_null(self.name.clone(), self.dtype(), n),
        };
        Series {
            name: self.name.clone(),
            data,
        }
    }

    // ---------- 去重 ----------

    /// 去重：依据 ``keep`` 策略保留重复值的代表行。
    ///
    /// - ``keep="first"``：保留每个值首次出现的位置（None 视为同一值，仅保留首个）。
    /// - ``keep="last"``：保留每个值末次出现的位置。
    /// - ``keep=False``（任意大小写形式或字面量 "False"）：删除所有重复值，
    ///   仅保留在整列中出现次数恰好为 1 的行。
    ///
    /// 实现细节：
    /// - Int64：使用 :struct:`HashSet<Option<i64>>`。
    /// - Float64：使用 :struct:`HashSet<Option<u64>>`（基于 f64::to_bits，确保
    ///   ``-0.0 == +0.0`` 且 NaN 视作同一值）。
    /// - Bool：使用 :struct:`HashSet<Option<bool>>`。
    /// - String：使用 :struct:`HashSet<Option<String>>`（按字符串内容比较）。
    /// - Categorical：基于 codes 去重，categories 保持原样。
    ///
    /// 不支持的 ``keep`` 值将默认按 ``"first"`` 处理。
    pub fn drop_duplicates(&self, keep: &str) -> Series {
        let n = self.len();
        if n == 0 {
            return self.clone();
        }

        // 解析 keep 参数（大小写不敏感）
        let keep_lower = keep.to_ascii_lowercase();
        // 0 = first, 1 = last, 2 = False（全部删除重复值）
        let mode: u8 = match keep_lower.as_str() {
            "first" => 0,
            "last" => 1,
            "false" => 2,
            _ => 0,
        };

        let mask: Vec<bool> = match &self.data {
            ColumnData::Int(v) => dup_mask(v, mode, |x| *x),
            ColumnData::Float(v) => {
                // 用 to_bits 将 f64 转为 u64，确保 -0.0/+0.0 与 NaN 行为一致
                dup_mask(v, mode, |x| x.map(|f| f.to_bits()))
            }
            ColumnData::Bool(v) => dup_mask(v, mode, |x| *x),
            ColumnData::String(v) => {
                // String 需要克隆才能放入 HashSet；这里用 Option<String> 作为 key
                let owned: Vec<Option<String>> = v.to_vec();
                dup_mask(&owned, mode, |x| x.clone())
            }
            ColumnData::Categorical(c) => dup_mask(&c.codes, mode, |x| *x),
        };

        // 用 mask 过滤原 Series
        self.filter(&mask)
    }

    /// 重复值标记：返回与 self 等长的 ``Vec<bool>``，``true`` 表示该位置为重复。
    ///
    /// 与 :meth:`drop_duplicates` 互补：``duplicated`` 标记的是 *被丢弃* 的行。
    ///
    /// - ``keep="first"``：除每个值的首次出现外，重复位置为 ``true``。
    /// - ``keep="last"``：除每个值的末次出现外，重复位置为 ``true``。
    /// - ``keep="false"``（任意大小写形式或字面量 "False"）：所有出现次数 > 1 的
    ///   位置都为 ``true``（即同一值的所有出现都标记为重复）。
    /// - 不支持的 ``keep`` 值默认按 ``"first"`` 处理。
    ///
    /// 实现复用 :func:`dup_mask`：先按相同策略生成"保留掩码"，再按位取反。
    pub fn duplicated_mask(&self, keep: &str) -> Vec<bool> {
        let n = self.len();
        if n == 0 {
            return Vec::new();
        }

        let keep_lower = keep.to_ascii_lowercase();
        let mode: u8 = match keep_lower.as_str() {
            "first" => 0,
            "last" => 1,
            "false" => 2,
            _ => 0,
        };

        let mask: Vec<bool> = match &self.data {
            ColumnData::Int(v) => dup_mask(v, mode, |x| *x),
            ColumnData::Float(v) => dup_mask(v, mode, |x| x.map(|f| f.to_bits())),
            ColumnData::Bool(v) => dup_mask(v, mode, |x| *x),
            ColumnData::String(v) => {
                let owned: Vec<Option<String>> = v.to_vec();
                dup_mask(&owned, mode, |x| x.clone())
            }
            ColumnData::Categorical(c) => dup_mask(&c.codes, mode, |x| *x),
        };

        // 取反得到"重复标记"
        mask.into_iter().map(|x| !x).collect()
    }

    /// 与 :meth:`duplicated_mask` 等价，但直接返回 :struct:`Series`（Bool 列），
    /// 避免 Python 层二次穿越（Rust → Vec → Python list → Rust Series）。
    ///
    /// 用于让 Python 层直接 ``_from_inner`` 包装结果，省去 ``Vec<bool>``
    /// → Python list → ``Series(mask, dtype="bool")`` 的双重边界穿越开销。
    pub fn duplicated_series(&self, keep: &str) -> Series {
        let mask = self.duplicated_mask(keep);
        let data = ColumnData::Bool(mask.into_iter().map(Some).collect());
        Series {
            name: self.name.clone(),
            data,
        }
    }

    /// 与 :meth:`drop_duplicates` 等价，但额外返回被保留行的原始位置索引。
    ///
    /// 用于让 Python 层跳过二次 mask 计算，直接通过 indices 构建新索引，
    /// 消除 Python 循环重建 mask 的开销（drop_duplicates 的主要瓶颈）。
    pub fn drop_duplicates_with_index(&self, keep: &str) -> (Series, Vec<usize>) {
        let n = self.len();
        if n == 0 {
            return (self.clone(), Vec::new());
        }

        let keep_lower = keep.to_ascii_lowercase();
        let mode: u8 = match keep_lower.as_str() {
            "first" => 0,
            "last" => 1,
            "false" => 2,
            _ => 0,
        };

        let mask: Vec<bool> = match &self.data {
            ColumnData::Int(v) => dup_mask(v, mode, |x| *x),
            ColumnData::Float(v) => dup_mask(v, mode, |x| x.map(|f| f.to_bits())),
            ColumnData::Bool(v) => dup_mask(v, mode, |x| *x),
            ColumnData::String(v) => {
                let owned: Vec<Option<String>> = v.to_vec();
                dup_mask(&owned, mode, |x| x.clone())
            }
            ColumnData::Categorical(c) => dup_mask(&c.codes, mode, |x| *x),
        };

        // 收集保留的位置索引（mask 中的 true 位置）
        let indices: Vec<usize> = mask
            .iter()
            .enumerate()
            .filter_map(|(i, &keep)| if keep { Some(i) } else { None })
            .collect();
        (self.filter(&mask), indices)
    }

    // ---------- 合并非空值 ----------

    /// 用 ``other`` 的非空值填充 self 的空值：``self[i]`` 为 None 且
    /// ``other[i]`` 非 None 时取 ``other[i]``，否则保留 ``self[i]``。
    ///
    /// 仅支持长度相同且 dtype 相同的 Int64/Float64/Bool/String 列。
    /// - dtype 不匹配 / 长度不同 / 任一为 Categorical → 返回 None（Python 层回退）。
    /// - dtype 相同但都是 Categorical 也返回 None：categories 集合可能不同，
    ///   直接合并 codes 会破坏语义，留给 Python 层处理。
    pub fn combine_first(&self, other: &Series) -> Option<Series> {
        // 长度必须相同
        if self.len() != other.len() {
            return None;
        }
        // dtype 必须相同
        if self.dtype() != other.dtype() {
            return None;
        }
        let n = self.len();

        let data = match (&self.data, &other.data) {
            (ColumnData::Int(a), ColumnData::Int(b)) => {
                let result: Vec<Option<i64>> = (0..n)
                    .into_par_iter()
                    .map(|i| match (a[i], b[i]) {
                        (Some(x), _) => Some(x),
                        (None, Some(y)) => Some(y),
                        (None, None) => None,
                    })
                    .collect();
                ColumnData::Int(result)
            }
            (ColumnData::Float(a), ColumnData::Float(b)) => {
                let result: Vec<Option<f64>> = (0..n)
                    .into_par_iter()
                    .map(|i| match (a[i], b[i]) {
                        (Some(x), _) => Some(x),
                        // 同时处理 NaN：self[i] 为 NaN 时也用 other[i] 替换（与 pandas 一致）
                        (None, Some(y)) => Some(y),
                        (None, None) => None,
                    })
                    .collect();
                ColumnData::Float(result)
            }
            (ColumnData::Bool(a), ColumnData::Bool(b)) => {
                let result: Vec<Option<bool>> = (0..n)
                    .into_par_iter()
                    .map(|i| match (a[i], b[i]) {
                        (Some(x), _) => Some(x),
                        (None, Some(y)) => Some(y),
                        (None, None) => None,
                    })
                    .collect();
                ColumnData::Bool(result)
            }
            (ColumnData::String(a), ColumnData::String(b)) => {
                let result: Vec<Option<String>> = (0..n)
                    .into_par_iter()
                    .map(|i| match (&a[i], &b[i]) {
                        (Some(x), _) => Some(x.clone()),
                        (None, Some(y)) => Some(y.clone()),
                        (None, None) => None,
                    })
                    .collect();
                ColumnData::String(result)
            }
            // Categorical 即便 dtype 相同也不直接合并（categories 可能不同）
            _ => return None,
        };
        Some(Series {
            name: self.name.clone(),
            data,
        })
    }

    // ---------- 众数 ----------

    /// 计算众数：返回出现次数最多的值（可能多个），按升序排列。
    ///
    /// 行为对齐 ``pandas.Series.mode``：
    /// - 跳过 None / NaN，仅统计非空值的出现次数。
    /// - 空列或全 None 列返回 None（由 Python 层回退到空 Series）。
    /// - 支持的 dtype：Int64 / Float64 / Bool / String / Categorical。
    /// - 返回的 Series 保留原列名，``data`` 为同 dtype 的众数列表。
    pub fn mode(&self) -> Option<Series> {
        let n = self.len();
        if n == 0 {
            return None;
        }

        // 收集 (值→次数) 并找出最大次数
        let (data, _max_count) = match &self.data {
            ColumnData::Int(v) => {
                let mut counts: HashMap<i64, usize> = HashMap::new();
                for x in v.iter().flatten() {
                    *counts.entry(*x).or_insert(0) += 1;
                }
                if counts.is_empty() {
                    return None;
                }
                let max_c = *counts.values().max().unwrap();
                let mut modes: Vec<i64> = counts
                    .into_iter()
                    .filter_map(|(k, c)| if c == max_c { Some(k) } else { None })
                    .collect();
                modes.sort_unstable();
                let result: Vec<Option<i64>> = modes.into_iter().map(Some).collect();
                (ColumnData::Int(result), max_c)
            }
            ColumnData::Float(v) => {
                let mut counts: HashMap<u64, (f64, usize)> = HashMap::new();
                for x in v.iter().flatten() {
                    let bits = x.to_bits();
                    let entry = counts.entry(bits).or_insert((*x, 0));
                    entry.1 += 1;
                }
                if counts.is_empty() {
                    return None;
                }
                let max_c = counts.values().map(|(_, c)| *c).max().unwrap();
                let mut modes: Vec<f64> = counts
                    .into_iter()
                    .filter_map(|(_, (val, c))| if c == max_c { Some(val) } else { None })
                    .collect();
                // 注意 NaN 视为同一值（按 to_bits 处理），不影响 max 计数
                modes.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
                let result: Vec<Option<f64>> = modes.into_iter().map(Some).collect();
                (ColumnData::Float(result), max_c)
            }
            ColumnData::Bool(v) => {
                // 仅两个可能值；用 [true_count, false_count] 计数
                let mut t = 0usize;
                let mut f = 0usize;
                for x in v.iter().flatten() {
                    if *x {
                        t += 1;
                    } else {
                        f += 1;
                    }
                }
                if t == 0 && f == 0 {
                    return None;
                }
                let max_c = t.max(f);
                let mut result: Vec<Option<bool>> = Vec::new();
                if f == max_c {
                    result.push(Some(false));
                }
                if t == max_c {
                    result.push(Some(true));
                }
                // 已升序排列：false 在前 true 在后
                (ColumnData::Bool(result), max_c)
            }
            ColumnData::String(v) => {
                let mut counts: HashMap<String, usize> = HashMap::new();
                for x in v.iter().flatten() {
                    *counts.entry(x.clone()).or_insert(0) += 1;
                }
                if counts.is_empty() {
                    return None;
                }
                let max_c = *counts.values().max().unwrap();
                let mut modes: Vec<String> = counts
                    .into_iter()
                    .filter_map(|(k, c)| if c == max_c { Some(k) } else { None })
                    .collect();
                modes.sort();
                let result: Vec<Option<String>> = modes.into_iter().map(Some).collect();
                (ColumnData::String(result), max_c)
            }
            // Categorical：基于 categories 计数，返回众数对应的分类名
            ColumnData::Categorical(c) => {
                let mut counts: HashMap<i32, usize> = HashMap::new();
                for code in c.codes.iter().flatten() {
                    *counts.entry(*code).or_insert(0) += 1;
                }
                if counts.is_empty() {
                    return None;
                }
                let max_c = *counts.values().max().unwrap();
                // 找出所有最大计数对应的 code，按 category 名称排序
                let mut modes_codes: Vec<i32> = counts
                    .into_iter()
                    .filter_map(|(code, cnt)| if cnt == max_c { Some(code) } else { None })
                    .collect();
                // 按 category 名排序（确保稳定顺序）
                modes_codes.sort_by(|&a, &b| {
                    let na = c.categories.get(a as usize).cloned().unwrap_or_default();
                    let nb = c.categories.get(b as usize).cloned().unwrap_or_default();
                    na.cmp(&nb)
                });
                let new_categories: Vec<String> = modes_codes
                    .iter()
                    .filter_map(|&code| c.categories.get(code as usize).cloned())
                    .collect();
                // 重新编码：每个众数在新 categories 中的索引
                let new_codes: Vec<Option<i32>> =
                    (0..new_categories.len() as i32).map(Some).collect();
                (
                    ColumnData::Categorical(CategoricalData {
                        categories: new_categories,
                        codes: new_codes,
                        ordered: c.ordered,
                    }),
                    max_c,
                )
            }
        };

        Some(Series {
            name: self.name.clone(),
            data,
        })
    }
}

// ---------- 模块私有辅助函数 ----------

/// 将字符串解析为 bool：接受 "true"/"false"（大小写不敏感）。
/// 其他输入返回 None（由调用方决定是否让 Python 回退）。
fn parse_bool_str(s: &str) -> Option<bool> {
    match s.to_ascii_lowercase().as_str() {
        "true" => Some(true),
        "false" => Some(false),
        _ => None,
    }
}

/// 通用去重掩码生成：根据 mode 计算每个位置是否保留。
///
/// - ``key_fn``：将 ``Option<T>`` 转换为可哈希的 key ``Option<K>``。
///   对于 f64，调用方传入 ``|x| x.map(|f| f.to_bits())``。
///
/// 返回与 ``values`` 等长的 ``Vec<bool>``，``true`` 表示保留该行。
fn dup_mask<T, K, F>(values: &[Option<T>], mode: u8, key_fn: F) -> Vec<bool>
where
    K: Eq + std::hash::Hash + Clone,
    F: Fn(&Option<T>) -> Option<K> + Sync,
{
    let n = values.len();
    match mode {
        // keep="first"：从前往后扫描，每个 key 首次出现时保留
        0 => {
            let mut seen: HashSet<Option<K>> = HashSet::new();
            values
                .iter()
                .map(|x| {
                    let key = key_fn(x);
                    seen.insert(key)
                })
                .collect()
        }
        // keep="last"：从后往前扫描，每个 key 首次出现时保留
        1 => {
            let mut seen: HashSet<Option<K>> = HashSet::new();
            let mut mask = vec![false; n];
            for i in (0..n).rev() {
                let key = key_fn(&values[i]);
                if seen.insert(key) {
                    mask[i] = true;
                }
            }
            mask
        }
        // keep=False：仅保留出现次数恰好为 1 的行
        2 => {
            // 先统计每个 key 的出现次数
            let mut counts: HashMap<Option<K>, usize> = HashMap::new();
            for x in values {
                let key = key_fn(x);
                *counts.entry(key).or_insert(0) += 1;
            }
            values
                .iter()
                .map(|x| {
                    let key = key_fn(x);
                    counts.get(&key).copied() == Some(1)
                })
                .collect()
        }
        _ => vec![true; n],
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::dtype::DType;

    #[test]
    fn test_replace_scalar_int() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(1), None, Some(3)]);
        let r = s.replace_scalar("1", "10").expect("Int 替换应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], Some(10));
            assert_eq!(v[1], Some(2));
            assert_eq!(v[2], Some(10));
            assert_eq!(v[3], None);
            assert_eq!(v[4], Some(3));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_replace_scalar_int_parse_fail() {
        let s = Series::new_int(None, vec![Some(1), Some(2)]);
        // old_str 无法 parse 为 i64 → 返回 None
        assert!(s.replace_scalar("1.5", "10").is_none());
    }

    #[test]
    fn test_replace_scalar_float() {
        let s = Series::new_float(None, vec![Some(1.5), Some(2.0), Some(1.5)]);
        let r = s.replace_scalar("1.5", "9.0").expect("Float 替换应成功");
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v[0], Some(9.0));
            assert_eq!(v[1], Some(2.0));
            assert_eq!(v[2], Some(9.0));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_replace_scalar_bool() {
        let s = Series::new_bool(None, vec![Some(true), Some(false), Some(true)]);
        let r = s.replace_scalar("true", "false").expect("Bool 替换应成功");
        if let ColumnData::Bool(v) = &r.data {
            assert_eq!(v, &vec![Some(false), Some(false), Some(false)]);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_replace_scalar_object_returns_none() {
        let s = Series::new_string(None, vec![Some("a".to_string()), Some("b".to_string())]);
        assert!(s.replace_scalar("a", "x").is_none());
    }

    #[test]
    fn test_replace_scalar_categorical() {
        let s = Series::new_categorical(
            None,
            vec!["low".to_string(), "mid".to_string(), "high".to_string()],
            vec![Some(0), Some(1), Some(2), Some(0), None],
            false,
        );
        let r = s
            .replace_scalar("low", "MIN")
            .expect("Categorical 替换应成功");
        if let ColumnData::Categorical(c) = &r.data {
            assert_eq!(c.categories[0], "MIN");
            assert_eq!(c.categories[1], "mid");
            assert_eq!(c.categories[2], "high");
            assert_eq!(c.codes[0], Some(0));
            assert_eq!(c.codes[3], Some(0));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_replace_dict_int() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(3), Some(1)]);
        let pairs = vec![
            ("1".to_string(), "10".to_string()),
            ("3".to_string(), "30".to_string()),
        ];
        let r = s.replace_dict(&pairs).expect("Int 批量替换应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v, &vec![Some(10), Some(2), Some(30), Some(10)]);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_replace_dict_float() {
        let s = Series::new_float(None, vec![Some(1.0), Some(2.0), Some(3.0)]);
        let pairs = vec![("1.0".to_string(), "10.0".to_string())];
        let r = s.replace_dict(&pairs).expect("Float 批量替换应成功");
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v[0], Some(10.0));
            assert_eq!(v[1], Some(2.0));
            assert_eq!(v[2], Some(3.0));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_replace_dict_bool() {
        let s = Series::new_bool(None, vec![Some(true), Some(false), Some(true)]);
        let pairs = vec![("true".to_string(), "false".to_string())];
        let r = s.replace_dict(&pairs).expect("Bool 批量替换应成功");
        if let ColumnData::Bool(v) = &r.data {
            assert_eq!(v, &vec![Some(false), Some(false), Some(false)]);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_replace_dict_object_returns_none() {
        let s = Series::new_string(None, vec![Some("a".to_string())]);
        let pairs = vec![("a".to_string(), "x".to_string())];
        assert!(s.replace_dict(&pairs).is_none());
    }

    #[test]
    fn test_diff_int_positive() {
        let s = Series::new_int(None, vec![Some(1), Some(3), Some(6), Some(10)]);
        let r = s.diff(1);
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], None);
            assert_eq!(v[1], Some(2)); // 3 - 1
            assert_eq!(v[2], Some(3)); // 6 - 3
            assert_eq!(v[3], Some(4)); // 10 - 6
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_diff_int_negative() {
        let s = Series::new_int(None, vec![Some(1), Some(3), Some(6), Some(10)]);
        let r = s.diff(-1);
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], Some(2)); // 3 - 1
            assert_eq!(v[1], Some(3)); // 6 - 3
            assert_eq!(v[2], Some(4)); // 10 - 6
            assert_eq!(v[3], None);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_diff_int_period_2() {
        let s = Series::new_int(None, vec![Some(1), Some(3), Some(6), Some(10), Some(15)]);
        let r = s.diff(2);
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], None);
            assert_eq!(v[1], None);
            assert_eq!(v[2], Some(5)); // 6 - 1
            assert_eq!(v[3], Some(7)); // 10 - 3
            assert_eq!(v[4], Some(9)); // 15 - 6
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_diff_int_zero() {
        let s = Series::new_int(None, vec![Some(1), Some(3), Some(6)]);
        let r = s.diff(0);
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], Some(1));
            assert_eq!(v[1], Some(3));
            assert_eq!(v[2], Some(6));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_diff_with_none() {
        let s = Series::new_int(None, vec![Some(1), None, Some(6)]);
        let r = s.diff(1);
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], None);
            assert_eq!(v[1], None); // None - 1
            assert_eq!(v[2], None); // 6 - None
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_diff_float() {
        let s = Series::new_float(None, vec![Some(1.5), Some(3.0), Some(6.0)]);
        let r = s.diff(1);
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v[0], None);
            assert_eq!(v[1], Some(1.5));
            assert_eq!(v[2], Some(3.0));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_diff_other_dtype_returns_all_none() {
        let s = Series::new_bool(None, vec![Some(true), Some(false)]);
        let r = s.diff(1);
        // Bool 列不支持 diff，返回全 None 的同 dtype Series
        assert_eq!(r.dtype(), DType::Bool);
        assert_eq!(r.len(), 2);
        if let ColumnData::Bool(v) = &r.data {
            assert_eq!(v[0], None);
            assert_eq!(v[1], None);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_diff_periods_exceeds_len() {
        let s = Series::new_int(None, vec![Some(1), Some(2)]);
        let r = s.diff(5);
        // |periods| >= len → 全 None
        assert_eq!(r.len(), 2);
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], None);
            assert_eq!(v[1], None);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_drop_duplicates_first() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(1), Some(3), Some(2)]);
        let r = s.drop_duplicates("first");
        if let ColumnData::Int(v) = &r.data {
            // 保留首次出现：1, 2, 3
            assert_eq!(v, &vec![Some(1), Some(2), Some(3)]);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_drop_duplicates_last() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(1), Some(3), Some(2)]);
        let r = s.drop_duplicates("last");
        if let ColumnData::Int(v) = &r.data {
            // 保留末次出现：1, 3, 2
            assert_eq!(v, &vec![Some(1), Some(3), Some(2)]);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_drop_duplicates_false() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(1), Some(3), Some(2)]);
        let r = s.drop_duplicates("False");
        if let ColumnData::Int(v) = &r.data {
            // 仅保留出现一次的：3
            assert_eq!(v, &vec![Some(3)]);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_drop_duplicates_with_none_first() {
        let s = Series::new_int(None, vec![Some(1), None, Some(2), None, Some(1)]);
        let r = s.drop_duplicates("first");
        if let ColumnData::Int(v) = &r.data {
            // None 视为同一值，仅保留首个：1, None, 2
            assert_eq!(v, &vec![Some(1), None, Some(2)]);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_drop_duplicates_float() {
        let s = Series::new_float(None, vec![Some(1.5), Some(2.0), Some(1.5), Some(3.0)]);
        let r = s.drop_duplicates("first");
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v, &vec![Some(1.5), Some(2.0), Some(3.0)]);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_drop_duplicates_bool() {
        let s = Series::new_bool(None, vec![Some(true), Some(false), Some(true)]);
        let r = s.drop_duplicates("first");
        if let ColumnData::Bool(v) = &r.data {
            assert_eq!(v, &vec![Some(true), Some(false)]);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_drop_duplicates_string() {
        let s = Series::new_string(
            None,
            vec![
                Some("a".to_string()),
                Some("b".to_string()),
                Some("a".to_string()),
            ],
        );
        let r = s.drop_duplicates("first");
        if let ColumnData::String(v) = &r.data {
            assert_eq!(v, &vec![Some("a".to_string()), Some("b".to_string())]);
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_drop_duplicates_categorical() {
        let s = Series::new_categorical(
            None,
            vec!["low".to_string(), "mid".to_string(), "high".to_string()],
            vec![Some(0), Some(1), Some(0), Some(2), Some(1)],
            false,
        );
        let r = s.drop_duplicates("first");
        // codes 0, 1, 2 各保留首个 → 长度 3
        assert_eq!(r.len(), 3);
        if let ColumnData::Categorical(c) = &r.data {
            assert_eq!(c.codes[0], Some(0));
            assert_eq!(c.codes[1], Some(1));
            assert_eq!(c.codes[2], Some(2));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_combine_first_int() {
        let a = Series::new_int(None, vec![Some(1), None, None, Some(4)]);
        let b = Series::new_int(None, vec![Some(10), Some(20), None, Some(40)]);
        let r = a.combine_first(&b).expect("Int combine_first 应成功");
        if let ColumnData::Int(v) = &r.data {
            assert_eq!(v[0], Some(1)); // a 非 None → 保留 a
            assert_eq!(v[1], Some(20)); // a None, b 非 None → 取 b
            assert_eq!(v[2], None); // a None, b None → None
            assert_eq!(v[3], Some(4));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_combine_first_float() {
        let a = Series::new_float(None, vec![Some(1.0), None, Some(3.0)]);
        let b = Series::new_float(None, vec![Some(10.0), Some(20.0), None]);
        let r = a.combine_first(&b).expect("Float combine_first 应成功");
        if let ColumnData::Float(v) = &r.data {
            assert_eq!(v[0], Some(1.0));
            assert_eq!(v[1], Some(20.0));
            assert_eq!(v[2], Some(3.0));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_combine_first_bool() {
        let a = Series::new_bool(None, vec![Some(true), None]);
        let b = Series::new_bool(None, vec![Some(false), Some(true)]);
        let r = a.combine_first(&b).expect("Bool combine_first 应成功");
        if let ColumnData::Bool(v) = &r.data {
            assert_eq!(v[0], Some(true));
            assert_eq!(v[1], Some(true));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_combine_first_string() {
        let a = Series::new_string(
            None,
            vec![Some("a".to_string()), None, Some("c".to_string())],
        );
        let b = Series::new_string(
            None,
            vec![
                Some("x".to_string()),
                Some("y".to_string()),
                Some("z".to_string()),
            ],
        );
        let r = a.combine_first(&b).expect("String combine_first 应成功");
        if let ColumnData::String(v) = &r.data {
            assert_eq!(v[0], Some("a".to_string()));
            assert_eq!(v[1], Some("y".to_string()));
            assert_eq!(v[2], Some("c".to_string()));
        } else {
            panic!("dtype 错误");
        }
    }

    #[test]
    fn test_combine_first_length_mismatch() {
        let a = Series::new_int(None, vec![Some(1), Some(2)]);
        let b = Series::new_int(None, vec![Some(1)]);
        assert!(a.combine_first(&b).is_none());
    }

    #[test]
    fn test_combine_first_dtype_mismatch() {
        let a = Series::new_int(None, vec![Some(1), Some(2)]);
        let b = Series::new_float(None, vec![Some(1.0), Some(2.0)]);
        assert!(a.combine_first(&b).is_none());
    }

    #[test]
    fn test_combine_first_categorical_returns_none() {
        let a = Series::new_categorical(None, vec!["a".to_string()], vec![Some(0)], false);
        let b = Series::new_categorical(None, vec!["a".to_string()], vec![Some(0)], false);
        // Categorical 即便 dtype 相同也返回 None
        assert!(a.combine_first(&b).is_none());
    }

    #[test]
    fn test_parse_bool_str() {
        assert_eq!(parse_bool_str("true"), Some(true));
        assert_eq!(parse_bool_str("True"), Some(true));
        assert_eq!(parse_bool_str("TRUE"), Some(true));
        assert_eq!(parse_bool_str("false"), Some(false));
        assert_eq!(parse_bool_str("False"), Some(false));
        assert_eq!(parse_bool_str("yes"), None);
        assert_eq!(parse_bool_str("1"), None);
    }
}
