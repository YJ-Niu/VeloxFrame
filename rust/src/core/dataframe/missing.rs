//! DataFrame 缺失值方法：行级缺失检测、全列填充、前后向填充。
//!
//! - isnull_rows / notnull_rows：返回每行是否有缺失值
//! - dropna：删除包含缺失值的行
//! - fillna_all_f64 / fillna_all_i64 / fillna_all_string：全列填充
//! - par_ffill_all / par_bfill_all：全列前后向填充

use rayon::prelude::*;

use crate::core::dataframe::DataFrame;
use crate::core::dtype::ColumnData;
use crate::core::series::Series;

impl DataFrame {
    /// 返回每行是否有缺失值
    pub fn isnull_rows(&self) -> Vec<bool> {
        let nrows = self.nrows();
        (0..nrows)
            .into_par_iter()
            .map(|i| {
                self.data.iter().any(|s| match &s.data {
                    ColumnData::Int(v) => v[i].is_none(),
                    ColumnData::Float(v) => v[i].is_none(),
                    ColumnData::Bool(v) => v[i].is_none(),
                    ColumnData::String(v) => v[i].is_none(),
                    ColumnData::Categorical(c) => c.codes[i].is_none(),
                })
            })
            .collect()
    }

    /// 返回每行是否全部非缺失
    pub fn notnull_rows(&self) -> Vec<bool> {
        let nrows = self.nrows();
        (0..nrows)
            .into_par_iter()
            .map(|i| {
                self.data.iter().all(|s| match &s.data {
                    ColumnData::Int(v) => v[i].is_some(),
                    ColumnData::Float(v) => v[i].is_some(),
                    ColumnData::Bool(v) => v[i].is_some(),
                    ColumnData::String(v) => v[i].is_some(),
                    ColumnData::Categorical(c) => c.codes[i].is_some(),
                })
            })
            .collect()
    }

    /// 删除包含缺失值的行
    pub fn dropna(&self) -> DataFrame {
        self.dropna_rows()
    }

    /// 填充所有列的缺失值 (f64，仅对 Float64 列生效)
    pub fn fillna_all_f64(&self, v: f64) -> DataFrame {
        let n_data: Vec<Series> = self.data.par_iter().map(|s| s.fillna_f64(v)).collect();
        DataFrame {
            columns: self.columns.clone(),
            data: n_data,
        }
    }

    /// 填充所有列的缺失值 (i64，仅对 Int64 列生效)
    pub fn fillna_all_i64(&self, v: i64) -> DataFrame {
        let n_data: Vec<Series> = self.data.par_iter().map(|s| s.fillna_i64(v)).collect();
        DataFrame {
            columns: self.columns.clone(),
            data: n_data,
        }
    }

    /// 填充所有列的缺失值 (string，仅对 Object 列生效)
    pub fn fillna_all_string(&self, v: &str) -> DataFrame {
        let n_data: Vec<Series> = self.data.par_iter().map(|s| s.fillna_string(v)).collect();
        DataFrame {
            columns: self.columns.clone(),
            data: n_data,
        }
    }

    /// 标量填充所有列：依据每列 dtype 自动选择 fillna_xxx，单次并行遍历。
    ///
    /// 与连续调用 fillna_all_i64 / fillna_all_f64 / fillna_all_string 不同，
    /// 本方法只遍历 columns 一次，且每列按自身 dtype 选择填充策略。
    /// 标量值预先 extract 为 4 个候选类型（i64/f64/bool/str），
    /// 每列只取与自身 dtype 匹配的候选，避免每列重复 extract Python 对象。
    /// 无法匹配的列保持原样（与 Series.fillna Rust 实现一致）。
    pub fn fillna_scalar(
        &self,
        v_i64: Option<i64>,
        v_f64: Option<f64>,
        v_bool: Option<bool>,
        v_str: Option<&str>,
    ) -> DataFrame {
        // 把字符串标量克隆为 owned，便于 'static 闭包
        let v_str_owned: Option<String> = v_str.map(|s| s.to_string());
        let n_data: Vec<Series> = self
            .data
            .par_iter()
            .map(|s| {
                let new_data = match &s.data {
                    // Int 列：优先用 i64 标量；其他类型不匹配，保持原样
                    ColumnData::Int(_) => v_i64.map_or(s.data.clone(), |v| s.fillna_i64(v).data),
                    // Float 列：优先用 f64 标量；i64 标量可转 f64
                    ColumnData::Float(_) => v_f64.map_or_else(
                        || v_i64.map_or(s.data.clone(), |v| s.fillna_f64(v as f64).data),
                        |v| s.fillna_f64(v).data,
                    ),
                    // Bool 列：仅接受 bool 标量，其他保持原样
                    ColumnData::Bool(_) => v_bool.map_or(s.data.clone(), |v| s.fillna_bool(v).data),
                    // String 列：优先 str；其他标量转字符串后填充
                    ColumnData::String(_) => {
                        if let Some(v) = &v_str_owned {
                            s.fillna_string(v).data
                        } else if let Some(v) = v_i64 {
                            s.fillna_string(&v.to_string()).data
                        } else if let Some(v) = v_f64 {
                            s.fillna_string(&v.to_string()).data
                        } else if let Some(v) = v_bool {
                            s.fillna_string(&v.to_string()).data
                        } else {
                            s.data.clone()
                        }
                    }
                    // Categorical 列：把标量转字符串后填充（fillna_categorical）
                    ColumnData::Categorical(_) => {
                        let s_val: Option<String> = v_str_owned
                            .clone()
                            .or_else(|| v_i64.map(|v| v.to_string()))
                            .or_else(|| v_f64.map(|v| v.to_string()))
                            .or_else(|| v_bool.map(|v| v.to_string()));
                        match s_val {
                            Some(v) => s.fillna_categorical(&v).data,
                            None => s.data.clone(),
                        }
                    }
                };
                Series {
                    name: s.name.clone(),
                    data: new_data,
                }
            })
            .collect();
        DataFrame {
            columns: self.columns.clone(),
            data: n_data,
        }
    }

    /// 所有列并行前向填充 (ffill)
    pub fn par_ffill_all(&self) -> DataFrame {
        let n_data: Vec<Series> = self.data.par_iter().map(|s| s.ffill()).collect();
        DataFrame {
            columns: self.columns.clone(),
            data: n_data,
        }
    }

    /// 所有列并行后向填充 (bfill)
    pub fn par_bfill_all(&self) -> DataFrame {
        let n_data: Vec<Series> = self.data.par_iter().map(|s| s.bfill()).collect();
        DataFrame {
            columns: self.columns.clone(),
            data: n_data,
        }
    }
}
