//! Series 聚合统计：count / sum / mean / min / max / std / var / median / any / all。
//!
//! 聚合语义与 主流库 默认行为对齐：
//! - 缺失值 (None 与 NaN) 一律跳过 (skipna=True)
//! - 空列或全缺失列返回 None；any/all 在空列上分别返回 false/true

use rayon::prelude::*;

use crate::core::dtype::ColumnData;
use crate::core::series::Series;

impl Series {
    // ---------- 聚合 ----------

    pub fn count(&self) -> usize {
        self.data.count_non_null()
    }

    pub fn sum_i64(&self) -> Option<i64> {
        if let ColumnData::Int(v) = &self.data {
            Some(v.par_iter().filter_map(|x| *x).sum())
        } else {
            None
        }
    }
    pub fn sum_f64(&self) -> Option<f64> {
        if let ColumnData::Float(v) = &self.data {
            Some(
                v.par_iter()
                    .filter_map(|x| *x)
                    .filter(|x| !x.is_nan())
                    .sum(),
            )
        } else {
            None
        }
    }
    pub fn sum_bool(&self) -> usize {
        if let ColumnData::Bool(v) = &self.data {
            v.par_iter().filter(|x| matches!(x, Some(true))).count()
        } else {
            0
        }
    }

    pub fn mean(&self) -> Option<f64> {
        // 过滤 None 和 NaN 后计算均值 (NaN 语义上等同缺失值)
        let (sum, cnt) = match &self.data {
            ColumnData::Int(v) => {
                let filtered: Vec<i64> = v.par_iter().filter_map(|x| *x).collect();
                let cnt = filtered.len();
                let s: i64 = filtered.into_par_iter().sum();
                (s as f64, cnt)
            }
            ColumnData::Float(v) => {
                let filtered: Vec<f64> = v
                    .par_iter()
                    .filter_map(|x| x.filter(|v| !v.is_nan()))
                    .collect();
                let cnt = filtered.len();
                let s: f64 = filtered.into_par_iter().sum();
                (s, cnt)
            }
            _ => return None,
        };
        if cnt == 0 {
            return None;
        }
        Some(sum / cnt as f64)
    }

    pub fn min_i64(&self) -> Option<i64> {
        if let ColumnData::Int(v) = &self.data {
            v.par_iter().filter_map(|x| *x).min()
        } else {
            None
        }
    }
    pub fn min_f64(&self) -> Option<f64> {
        if let ColumnData::Float(v) = &self.data {
            // 过滤 None 和 NaN (NaN 语义上等同缺失值)
            v.par_iter()
                .filter_map(|x| x.filter(|v| !v.is_nan()))
                .min_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal))
        } else {
            None
        }
    }
    pub fn min_str(&self) -> Option<String> {
        if let ColumnData::String(v) = &self.data {
            v.par_iter().filter_map(|x| x.clone()).min()
        } else {
            None
        }
    }
    pub fn max_i64(&self) -> Option<i64> {
        if let ColumnData::Int(v) = &self.data {
            v.par_iter().filter_map(|x| *x).max()
        } else {
            None
        }
    }
    pub fn max_f64(&self) -> Option<f64> {
        if let ColumnData::Float(v) = &self.data {
            // 过滤 None 和 NaN (NaN 语义上等同缺失值)
            v.par_iter()
                .filter_map(|x| x.filter(|v| !v.is_nan()))
                .max_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal))
        } else {
            None
        }
    }
    pub fn max_str(&self) -> Option<String> {
        if let ColumnData::String(v) = &self.data {
            v.par_iter().filter_map(|x| x.clone()).max()
        } else {
            None
        }
    }

    pub fn std(&self) -> Option<f64> {
        self.var().map(|v| v.sqrt())
    }
    pub fn var(&self) -> Option<f64> {
        let m = self.mean()?;
        // 使用过滤后的非 NaN 值计算方差 (与 mean 保持一致)
        let (sum_sq, cnt) = match &self.data {
            ColumnData::Int(v) => {
                let filtered: Vec<i64> = v.par_iter().filter_map(|x| *x).collect();
                let cnt = filtered.len();
                let s: f64 = filtered
                    .into_par_iter()
                    .map(|x| (x as f64 - m).powi(2))
                    .sum();
                (s, cnt)
            }
            ColumnData::Float(v) => {
                let filtered: Vec<f64> = v
                    .par_iter()
                    .filter_map(|x| x.filter(|v| !v.is_nan()))
                    .collect();
                let cnt = filtered.len();
                let s: f64 = filtered.into_par_iter().map(|x| (x - m).powi(2)).sum();
                (s, cnt)
            }
            _ => return None,
        };
        if cnt == 0 {
            return None;
        }
        Some(sum_sq / cnt as f64)
    }
    pub fn median(&self) -> Option<f64> {
        // 过滤 None 和 NaN 后计算中位数
        let mut vs: Vec<f64> = match &self.data {
            ColumnData::Int(v) => v.par_iter().filter_map(|x| *x).map(|x| x as f64).collect(),
            ColumnData::Float(v) => v
                .par_iter()
                .filter_map(|x| x.filter(|v| !v.is_nan()))
                .collect(),
            _ => return None,
        };
        if vs.is_empty() {
            return None;
        }
        vs.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let n = vs.len();
        if n % 2 == 1 {
            Some(vs[n / 2])
        } else {
            Some((vs[n / 2 - 1] + vs[n / 2]) / 2.0)
        }
    }

    pub fn any(&self) -> Option<bool> {
        let r: bool = match &self.data {
            ColumnData::Bool(v) => v.par_iter().filter_map(|x| *x).any(|x| x),
            ColumnData::Int(v) => v.par_iter().filter_map(|x| *x).any(|x| x != 0),
            ColumnData::Float(v) => v.par_iter().filter_map(|x| *x).any(|x| x != 0.0),
            ColumnData::String(v) => v
                .par_iter()
                .filter_map(|x| x.clone())
                .any(|s| !s.is_empty()),
            ColumnData::Categorical(c) => c.codes.par_iter().any(|x| x.is_some()),
        };
        Some(r)
    }
    pub fn all(&self) -> Option<bool> {
        // 空列：all 返回 True（与 主流库 一致）
        // 有缺失值：skipna=True（默认）跳过 None；全为 None 则返回 True
        let r: bool = match &self.data {
            ColumnData::Bool(v) => v.par_iter().filter_map(|x| *x).all(|x| x),
            ColumnData::Int(v) => v.par_iter().filter_map(|x| *x).all(|x| x != 0),
            ColumnData::Float(v) => v.par_iter().filter_map(|x| *x).all(|x| x != 0.0),
            ColumnData::String(v) => v
                .par_iter()
                .filter_map(|x| x.clone())
                .all(|s| !s.is_empty()),
            ColumnData::Categorical(c) => {
                // 分类列：所有非 None 视为 True
                c.codes.par_iter().all(|x| x.is_some())
            }
        };
        Some(r)
    }

    // ---------- 位置索引 ----------

    /// 返回最大值首次出现的位置索引（None 视为缺失，NaN 视为缺失）。
    /// 全空或空列返回 None。
    /// Categorical 列返回 None（由 Python 层按 category 字符串比较）。
    pub fn argmax(&self) -> Option<usize> {
        match &self.data {
            ColumnData::Int(v) => argmax_i64(v),
            ColumnData::Float(v) => argmax_f64(v),
            ColumnData::Bool(v) => argmax_bool(v),
            ColumnData::String(v) => argmax_string(v),
            ColumnData::Categorical(_) => None,
        }
    }

    /// 返回最小值首次出现的位置索引（None 视为缺失，NaN 视为缺失）。
    /// 全空或空列返回 None。
    /// Categorical 列返回 None（由 Python 层按 category 字符串比较）。
    pub fn argmin(&self) -> Option<usize> {
        match &self.data {
            ColumnData::Int(v) => argmin_i64(v),
            ColumnData::Float(v) => argmin_f64(v),
            ColumnData::Bool(v) => argmin_bool(v),
            ColumnData::String(v) => argmin_string(v),
            ColumnData::Categorical(_) => None,
        }
    }

    // ---------- 高阶矩 ----------

    /// 样本偏度（3 阶中心矩）。
    /// - skipna=True：跳过 None 和 NaN
    /// - n < 3 时返回 None
    /// - bias=false 时进行无偏修正
    pub fn skew(&self, bias: bool) -> Option<f64> {
        let filtered = self.collect_non_null_f64()?;
        let n = filtered.len();
        if n < 3 {
            return None;
        }
        let m = filtered.iter().sum::<f64>() / n as f64;
        let var = filtered.iter().map(|x| (x - m).powi(2)).sum::<f64>() / n as f64;
        if var == 0.0 {
            return Some(0.0);
        }
        let std = var.sqrt();
        let g = filtered.iter().map(|x| (x - m).powi(3)).sum::<f64>() / (n as f64 * std.powi(3));
        let result = if !bias {
            // 无偏修正（与 主流库/scipy 一致）：sqrt(n*(n-1)) / (n-2)
            g * ((n * (n - 1)) as f64).sqrt() / (n - 2) as f64
        } else {
            g
        };
        Some(result)
    }

    /// 样本峰度（4 阶中心矩）。
    /// - skipna=True：跳过 None 和 NaN
    /// - n < 4 时返回 None
    /// - bias=false 时进行无偏修正
    /// - fisher=false 时返回 Pearson 峰度（Fisher 峰度 + 3）
    pub fn kurt(&self, bias: bool, fisher: bool) -> Option<f64> {
        let filtered = self.collect_non_null_f64()?;
        let n = filtered.len();
        if n < 4 {
            return None;
        }
        let m = filtered.iter().sum::<f64>() / n as f64;
        let var = filtered.iter().map(|x| (x - m).powi(2)).sum::<f64>() / n as f64;
        if var == 0.0 {
            return Some(0.0);
        }
        let std = var.sqrt();
        let mut g2 =
            filtered.iter().map(|x| (x - m).powi(4)).sum::<f64>() / (n as f64 * std.powi(4)) - 3.0;
        if !bias && n > 3 {
            let factor = ((n - 1) * (n + 1)) as f64 / ((n - 2) * (n - 3)) as f64;
            g2 = factor * (g2 + 6.0 / (n as f64 + 1.0));
        }
        if !fisher {
            g2 += 3.0;
        }
        Some(g2)
    }

    // ---------- 平均绝对偏差 ----------

    /// 平均绝对偏差：mean(|x - mean(x)|)
    /// 跳过 None 和 NaN；空列返回 None。
    pub fn mad(&self) -> Option<f64> {
        let filtered = self.collect_non_null_f64()?;
        let n = filtered.len();
        if n == 0 {
            return None;
        }
        let m = filtered.iter().sum::<f64>() / n as f64;
        Some(filtered.iter().map(|x| (x - m).abs()).sum::<f64>() / n as f64)
    }

    // ---------- 成对统计 (corr / cov) ----------

    /// 两个 Series 的成对统计（两遍法）：在双方均非缺失的位置上
    /// （排除 NaN，与纯 Python 实现的配对语义一致），返回
    /// ``(n, sum((x-mx)(y-my)), sum((x-mx)^2), sum((y-my)^2))``。
    /// 长度不一致或无有效配对时返回 None。
    pub fn pair_stats(&self, other: &Series) -> Option<(usize, f64, f64, f64)> {
        let a = self.as_f64_vec();
        let b = other.as_f64_vec();
        if a.len() != b.len() || a.is_empty() {
            return None;
        }
        let mut n = 0usize;
        let mut sa = 0.0f64;
        let mut sb = 0.0f64;
        for (x, y) in a.iter().zip(b.iter()) {
            let (Some(x), Some(y)) = (x, y) else {
                continue;
            };
            if x.is_nan() || y.is_nan() {
                continue;
            }
            n += 1;
            sa += x;
            sb += y;
        }
        if n == 0 {
            return None;
        }
        let mx = sa / n as f64;
        let my = sb / n as f64;
        let mut cov = 0.0f64;
        let mut var_a = 0.0f64;
        let mut var_b = 0.0f64;
        for (x, y) in a.iter().zip(b.iter()) {
            let (Some(x), Some(y)) = (x, y) else {
                continue;
            };
            if x.is_nan() || y.is_nan() {
                continue;
            }
            let dx = x - mx;
            let dy = y - my;
            cov += dx * dy;
            var_a += dx * dx;
            var_b += dy * dy;
        }
        Some((n, cov, var_a, var_b))
    }

    /// 与 other 的样本协方差 (ddof 修正)：sum((x-mx)(y-my)) / (n - ddof)。
    /// 非数值列或 n <= ddof 时返回 None。
    pub fn cov(&self, other: &Series, ddof: usize) -> Option<f64> {
        let (n, cov, _, _) = self.pair_stats(other)?;
        if n <= ddof {
            return None;
        }
        Some(cov / (n - ddof) as f64)
    }

    /// 与 other 的 Pearson 相关系数。
    /// 非数值列或任一方差为 0 时返回 None。
    pub fn corr(&self, other: &Series) -> Option<f64> {
        let (_, cov, var_a, var_b) = self.pair_stats(other)?;
        if var_a <= 0.0 || var_b <= 0.0 {
            return None;
        }
        Some(cov / (var_a.sqrt() * var_b.sqrt()))
    }

    // ---------- 自相关 ----------

    /// 计算 lag 阶自相关系数。
    /// - 跳过 None 与 NaN（与 主流库 Series.autocorr 一致）
    /// - n <= lag 时返回 None
    /// - 任一截尾方差为 0 时返回 None
    pub fn autocorr(&self, lag: usize) -> Option<f64> {
        let filtered = self.collect_non_null_f64()?;
        let n = filtered.len();
        if n <= lag {
            return None;
        }
        let s1 = &filtered[..n - lag];
        let s2 = &filtered[lag..];
        let m1 = s1.iter().sum::<f64>() / s1.len() as f64;
        let m2 = s2.iter().sum::<f64>() / s2.len() as f64;
        let num = s1
            .iter()
            .zip(s2.iter())
            .map(|(a, b)| (a - m1) * (b - m2))
            .sum::<f64>();
        let den1 = s1.iter().map(|a| (a - m1).powi(2)).sum::<f64>().sqrt();
        let den2 = s2.iter().map(|b| (b - m2).powi(2)).sum::<f64>().sqrt();
        if den1 == 0.0 || den2 == 0.0 {
            return None;
        }
        Some(num / (den1 * den2))
    }

    // ---------- 乘积 ----------

    /// Int64 列所有非空值的乘积；其他列返回 None。
    /// 空列返回 Some(1)（与 主流库 min_count=0 一致）。
    pub fn prod_i64(&self) -> Option<i64> {
        if let ColumnData::Int(v) = &self.data {
            let mut acc: i64 = 1;
            for x in v.iter().flatten() {
                acc *= x;
            }
            Some(acc)
        } else {
            None
        }
    }

    /// Float64 列所有非空非 NaN 值的乘积；其他列返回 None。
    /// 空列返回 Some(1.0)。
    pub fn prod_f64(&self) -> Option<f64> {
        if let ColumnData::Float(v) = &self.data {
            let mut acc: f64 = 1.0;
            for x in v.iter().flatten() {
                if !x.is_nan() {
                    acc *= x;
                }
            }
            Some(acc)
        } else {
            None
        }
    }

    // ---------- 内部辅助 ----------

    /// 收集所有非空非 NaN 的 f64 值；非数值列返回 None。
    fn collect_non_null_f64(&self) -> Option<Vec<f64>> {
        let v = match &self.data {
            ColumnData::Int(v) => v.iter().filter_map(|x| *x).map(|x| x as f64).collect(),
            ColumnData::Float(v) => v.iter().filter_map(|x| x.filter(|v| !v.is_nan())).collect(),
            _ => return None,
        };
        Some(v)
    }
}

// ---------- argmax / argmin 自由函数 ----------

fn argmax_i64(v: &[Option<i64>]) -> Option<usize> {
    let mut best: Option<(usize, i64)> = None;
    for (i, x) in v.iter().enumerate() {
        if let Some(val) = x {
            match &best {
                None => best = Some((i, *val)),
                Some((_, bv)) if *val > *bv => best = Some((i, *val)),
                _ => {}
            }
        }
    }
    best.map(|(i, _)| i)
}

fn argmin_i64(v: &[Option<i64>]) -> Option<usize> {
    let mut best: Option<(usize, i64)> = None;
    for (i, x) in v.iter().enumerate() {
        if let Some(val) = x {
            match &best {
                None => best = Some((i, *val)),
                Some((_, bv)) if *val < *bv => best = Some((i, *val)),
                _ => {}
            }
        }
    }
    best.map(|(i, _)| i)
}

fn argmax_f64(v: &[Option<f64>]) -> Option<usize> {
    let mut best: Option<(usize, f64)> = None;
    for (i, x) in v.iter().enumerate() {
        if let Some(val) = x {
            if val.is_nan() {
                continue;
            }
            match &best {
                None => best = Some((i, *val)),
                Some((_, bv)) if *val > *bv => best = Some((i, *val)),
                _ => {}
            }
        }
    }
    best.map(|(i, _)| i)
}

fn argmin_f64(v: &[Option<f64>]) -> Option<usize> {
    let mut best: Option<(usize, f64)> = None;
    for (i, x) in v.iter().enumerate() {
        if let Some(val) = x {
            if val.is_nan() {
                continue;
            }
            match &best {
                None => best = Some((i, *val)),
                Some((_, bv)) if *val < *bv => best = Some((i, *val)),
                _ => {}
            }
        }
    }
    best.map(|(i, _)| i)
}

fn argmax_bool(v: &[Option<bool>]) -> Option<usize> {
    // true 是最大值，返回首个 true；若无 true 则返回首个 false（仅当至少有一个 false 时）
    for (i, x) in v.iter().enumerate() {
        if matches!(x, Some(true)) {
            return Some(i);
        }
    }
    v.iter().position(|x| matches!(x, Some(false)))
}

fn argmin_bool(v: &[Option<bool>]) -> Option<usize> {
    // false 是最小值，返回首个 false；若无 false 则返回首个 true
    for (i, x) in v.iter().enumerate() {
        if matches!(x, Some(false)) {
            return Some(i);
        }
    }
    v.iter().position(|x| matches!(x, Some(true)))
}

fn argmax_string(v: &[Option<String>]) -> Option<usize> {
    let mut best: Option<(usize, &String)> = None;
    for (i, x) in v.iter().enumerate() {
        if let Some(val) = x {
            match &best {
                None => best = Some((i, val)),
                Some((_, bv)) if val > *bv => best = Some((i, val)),
                _ => {}
            }
        }
    }
    best.map(|(i, _)| i)
}

fn argmin_string(v: &[Option<String>]) -> Option<usize> {
    let mut best: Option<(usize, &String)> = None;
    for (i, x) in v.iter().enumerate() {
        if let Some(val) = x {
            match &best {
                None => best = Some((i, val)),
                Some((_, bv)) if val < *bv => best = Some((i, val)),
                _ => {}
            }
        }
    }
    best.map(|(i, _)| i)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::dtype::DType;

    #[test]
    fn test_argmax_argmin_int() {
        let s = Series::new_int(None, vec![Some(3), Some(1), Some(4), Some(1), None]);
        assert_eq!(s.argmax(), Some(2));
        assert_eq!(s.argmin(), Some(1)); // 首个最小值
    }

    #[test]
    fn test_argmax_argmin_float_with_nan() {
        let s = Series::new_float(
            None,
            vec![Some(1.5), Some(f64::NAN), Some(3.0), Some(2.0), None],
        );
        assert_eq!(s.argmax(), Some(2));
        assert_eq!(s.argmin(), Some(0));
    }

    #[test]
    fn test_argmax_argmin_bool() {
        let s = Series::new_bool(None, vec![Some(false), Some(true), Some(false)]);
        assert_eq!(s.argmax(), Some(1)); // 首个 true
        assert_eq!(s.argmin(), Some(0)); // 首个 false
    }

    #[test]
    fn test_argmax_argmin_string() {
        let s = Series::new_string(
            None,
            vec![
                Some("banana".into()),
                Some("apple".into()),
                Some("cherry".into()),
            ],
        );
        assert_eq!(s.argmax(), Some(2)); // cherry 最大
        assert_eq!(s.argmin(), Some(1)); // apple 最小
    }

    #[test]
    fn test_argmax_all_none() {
        let s = Series::new_int(None, vec![None, None]);
        assert_eq!(s.argmax(), None);
        assert_eq!(s.argmin(), None);
    }

    #[test]
    fn test_skew_basic() {
        // 简单对称分布 → 偏度接近 0
        let s = Series::new_float(None, (1..=5).map(|i| Some(i as f64)).collect::<Vec<_>>());
        let v = s.skew(true).expect("skew 应返回值");
        assert!(v.abs() < 1e-9, "对称分布偏度应≈0, got {v}");
    }

    #[test]
    fn test_skew_too_few() {
        let s = Series::new_float(None, vec![Some(1.0), Some(2.0)]);
        assert_eq!(s.skew(true), None);
    }

    #[test]
    fn test_kurt_basic() {
        // 均匀分布峰度 < 0（Fisher）
        let s = Series::new_float(None, (1..=7).map(|i| Some(i as f64)).collect::<Vec<_>>());
        let v = s.kurt(true, true).expect("kurt 应返回值");
        assert!(v < 0.0, "均匀分布 Fisher 峰度 < 0, got {v}");
    }

    #[test]
    fn test_kurt_pearson() {
        // Pearson 峰度 = Fisher + 3
        let s = Series::new_float(None, (1..=10).map(|i| Some(i as f64)).collect::<Vec<_>>());
        let f = s.kurt(true, true).unwrap();
        let p = s.kurt(true, false).unwrap();
        assert!((p - f - 3.0).abs() < 1e-9);
    }

    #[test]
    fn test_mad() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(3), Some(4), Some(5)]);
        let v = s.mad().expect("mad 应返回值");
        assert!((v - 1.2).abs() < 1e-9, "mad 应为 1.2, got {v}");
    }

    #[test]
    fn test_autocorr_identity() {
        // lag=0 时 s1 == s2，相关系数 = 1.0
        let s = Series::new_int(None, (1..=10).map(Some).collect::<Vec<_>>());
        let v = s.autocorr(0).expect("autocorr(0) 应有值");
        assert!((v - 1.0).abs() < 1e-9, "autocorr(0) = 1.0, got {v}");
    }

    #[test]
    fn test_autocorr_too_short() {
        let s = Series::new_int(None, vec![Some(1), Some(2)]);
        assert_eq!(s.autocorr(5), None);
    }

    #[test]
    fn test_prod_i64() {
        let s = Series::new_int(None, vec![Some(1), Some(2), Some(3), Some(4), None]);
        assert_eq!(s.prod_i64(), Some(24));
    }

    #[test]
    fn test_prod_f64_with_nan() {
        let s = Series::new_float(None, vec![Some(2.0), Some(f64::NAN), Some(3.0), None]);
        assert_eq!(s.prod_f64(), Some(6.0));
    }

    #[test]
    fn test_prod_empty() {
        let s = Series::new_int(None, vec![]);
        assert_eq!(s.prod_i64(), Some(1));
        let s2 = Series::new_float(None, vec![]);
        assert_eq!(s2.prod_f64(), Some(1.0));
    }

    #[test]
    fn test_argmin_categorical_returns_none() {
        let s = Series::new_categorical(
            None,
            vec!["a".into(), "b".into()],
            vec![Some(0), Some(1)],
            false,
        );
        assert_eq!(s.argmin(), None);
        assert_eq!(s.argmax(), None);
        let _ = DType::Categorical; // 仅占位避免未用告警
    }
}
