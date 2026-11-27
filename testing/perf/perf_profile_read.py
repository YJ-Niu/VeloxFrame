"""分析 read_csv 各阶段耗时"""
import time
import veloxframe as pd
from veloxframe import veloxframe as _rust
from veloxframe.io._common import _infer_column_type

col_1 = list(range(500000)) + ["a", "b"] + list(range(500000))
df = pd.DataFrame({"col_1": col_1})
df.to_csv("./testing/foo.csv")

path = "./testing/foo.csv"

default_na = {
    "", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan",
    "1.#IND", "1.#QNAN", "<NA>", "N/A", "NA", "NULL", "NaN", "None",
    "n/a", "nan", "null",
}

t0 = time.time()
rust_headers, cols_data = _rust.read_csv_path_raw(
    path, True,
    delimiter=ord(','), quote=ord('"'), quoting=True,
    double_quote=True, escape=None, skip_initial_space=False,
    comment=None, skip_blank_lines=True, skiprows=None, skipfooter=None,
    lineterminator=None,
)
t1 = time.time()
print(f"1. Rust read_csv_path_raw: {t1-t0:.4f}s")

col = cols_data[1]  # col_1 数据列 (索引0是表头列名)
print("cols_data len:", len(cols_data), "col len:", len(col))

# NA filter
na_set = default_na
t2 = time.time()
if any(v in na_set for v in col):
    col = [None if v in na_set else v for v in col]
t3 = time.time()
print(f"2. NA filter (any + replace): {t3-t2:.4f}s")

# type inference
t4 = time.time()
inferred = _infer_column_type(col)
t5 = time.time()
print(f"3. _infer_column_type: {t5-t4:.4f}s")

# DataFrame construction
data = {"col_1": inferred}
t6 = time.time()
df2 = pd.DataFrame(data)
t7 = time.time()
print(f"4. DataFrame(data): {t7-t6:.4f}s")

# apply(type) + value_counts
t8 = time.time()
res = df2["col_1"].apply(type).value_counts()
t9 = time.time()
print(f"5. apply(type).value_counts(): {t9-t8:.4f}s")
print(res)