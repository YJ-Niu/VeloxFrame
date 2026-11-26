//! Series 比较运算：返回布尔掩码 (`Vec<bool>`) 的标量比较方法。
//!
//! 这些方法仅对匹配 dtype 的列产生有效掩码，其他类型返回全 false，
//! 与 pandas 中类型不匹配时静默不命中的语义保持一致。

use rayon::prelude::*;

use crate::core::dtype::ColumnData;
use crate::core::series::Series;

impl Series {
    // ---------- 比较 (返回 mask) ----------

    pub fn eq_scalar_i64(&self, v: i64) -> Vec<bool> {
        match &self.data {
            ColumnData::Int(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if *x == v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }
    pub fn eq_scalar_f64(&self, v: f64) -> Vec<bool> {
        match &self.data {
            ColumnData::Float(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if *x == v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }
    pub fn eq_scalar_bool(&self, v: bool) -> Vec<bool> {
        match &self.data {
            ColumnData::Bool(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if *x == v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }
    pub fn eq_scalar_str(&self, v: &str) -> Vec<bool> {
        match &self.data {
            ColumnData::String(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if x == v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }

    pub fn gt_scalar_i64(&self, v: i64) -> Vec<bool> {
        match &self.data {
            ColumnData::Int(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if *x > v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }
    pub fn gt_scalar_f64(&self, v: f64) -> Vec<bool> {
        match &self.data {
            ColumnData::Float(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if *x > v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }
    pub fn lt_scalar_i64(&self, v: i64) -> Vec<bool> {
        match &self.data {
            ColumnData::Int(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if *x < v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }
    pub fn lt_scalar_f64(&self, v: f64) -> Vec<bool> {
        match &self.data {
            ColumnData::Float(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if *x < v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }
    pub fn ge_scalar_i64(&self, v: i64) -> Vec<bool> {
        match &self.data {
            ColumnData::Int(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if *x >= v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }
    pub fn ge_scalar_f64(&self, v: f64) -> Vec<bool> {
        match &self.data {
            ColumnData::Float(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if *x >= v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }
    pub fn le_scalar_i64(&self, v: i64) -> Vec<bool> {
        match &self.data {
            ColumnData::Int(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if *x <= v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }
    pub fn le_scalar_f64(&self, v: f64) -> Vec<bool> {
        match &self.data {
            ColumnData::Float(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(x) if *x <= v))
                .collect(),
            _ => vec![false; self.len()],
        }
    }

    // ---------- 集合成员判断 (isin) ----------
    //
    // 接受目标 dtype 的 Vec，构造 HashSet 后并行检查每个元素是否在集合中。
    // 仅匹配 dtype 的列产生有效掩码，其他类型返回全 false（与现有 eq_scalar_*
    // 行为一致），Python 层据此回退到通用实现。

    /// Int64 列的成员判断。其他 dtype 返回全 false。
    pub fn isin_i64(&self, values: Vec<i64>) -> Vec<bool> {
        let set: std::collections::HashSet<i64> = values.into_iter().collect();
        match &self.data {
            ColumnData::Int(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(v) if set.contains(v)))
                .collect(),
            _ => vec![false; self.len()],
        }
    }

    /// Float64 列的成员判断。其他 dtype 返回全 false。
    /// NaN 永远不命中（NaN != NaN），与 Python `nan in {nan}` 返回 False 一致。
    pub fn isin_f64(&self, values: Vec<f64>) -> Vec<bool> {
        let set: std::collections::HashSet<u64> = values.into_iter().map(|f| f.to_bits()).collect();
        match &self.data {
            ColumnData::Float(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(v) if set.contains(&v.to_bits())))
                .collect(),
            _ => vec![false; self.len()],
        }
    }

    /// Bool 列的成员判断。其他 dtype 返回全 false。
    pub fn isin_bool(&self, values: Vec<bool>) -> Vec<bool> {
        let set: std::collections::HashSet<bool> = values.into_iter().collect();
        match &self.data {
            ColumnData::Bool(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(v) if set.contains(v)))
                .collect(),
            _ => vec![false; self.len()],
        }
    }

    /// String 列的成员判断。其他 dtype 返回全 false。
    pub fn isin_string(&self, values: Vec<String>) -> Vec<bool> {
        let set: std::collections::HashSet<String> = values.into_iter().collect();
        match &self.data {
            ColumnData::String(col) => col
                .par_iter()
                .map(|x| matches!(x, Some(v) if set.contains(v)))
                .collect(),
            _ => vec![false; self.len()],
        }
    }
}
