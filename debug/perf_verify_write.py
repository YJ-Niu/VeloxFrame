"""验证 Rust write_csv_string 与 Python to_csv 输出一致性"""
import rspandas as pd
from rspandas.rspandas import write_csv_string, write_csv_path
from rspandas.rspandas import _Series as _PySeries

col_1 = list(range(500000)) + ["a", "b"] + list(range(500000))
df = pd.DataFrame({"col_1": col_1})

# 当前 Python to_csv 输出
py_out = df.to_csv(None)
print("Python to_csv 前 2 行 + 中段 + 末尾:")
print(repr(py_out[:40]))
print(repr(py_out[499990:500030]))
print(repr(py_out[-40:]))

# Rust 路径:
series_list = [df._inner.get_column("col_1")]
idx_series = _PySeries(df._index, "")
columns_to_write = ["", "col_1"]
series_to_write = [idx_series] + series_list

rust_out = write_csv_string(columns_to_write, series_to_write, True, ",")
print("\nRust write_csv_string:")
print(repr(rust_out[:40]))
print(repr(rust_out[499990:500030]))
print(repr(rust_out[-40:]))

print("\n是否一致:", py_out == rust_out)
print("Python 长度:", len(py_out), "Rust 长度:", len(rust_out))