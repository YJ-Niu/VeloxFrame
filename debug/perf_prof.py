"""精细剖析 read_csv / apply(type) / value_counts 耗时"""
import time
import rspandas as pd
from rspandas.rspandas import read_csv_path_raw
from rspandas.io._common import _infer_column_type

col_1 = list(range(500000)) + ["a", "b"] + list(range(500000))
df = pd.DataFrame({"col_1": col_1})

t0 = time.time()
df.to_csv("./testing/foo.csv")
t_write = time.time()

# --- read_csv 拆分 ---
t1 = time.time()
rust_headers, cols_data = read_csv_path_raw(
    "./testing/foo.csv", True, delimiter=ord(","), quote=ord('"'), quoting=True,
    double_quote=True, escape=None, skip_initial_space=False, comment=None,
    skip_blank_lines=True, skiprows=None, skipfooter=None, lineterminator=None,
)
t_rust = time.time()

col_vals = cols_data[0]
t2 = time.time()
col_inferred = _infer_column_type(col_vals)
t_infer = time.time()

t3 = time.time()
df2 = pd.DataFrame({"col_1": col_inferred})
t_construct = time.time()

# --- apply / value_counts 拆分 ---
s = df2["col_1"]
t4 = time.time()
s_type = s.apply(type)
t_apply = time.time()

t5 = time.time()
s_type_inner = s_type._inner
vc = s_type.value_counts()
t_vc = time.time()

print(f"to_csv:            {t_write - t0:.4f}s")
print(f"  read_csv_path_raw: {t_rust - t1:.4f}s  (rows={len(col_vals)})")
print(f"  _infer_column_type: {t_infer - t2:.4f}s")
print(f"  DataFrame构造:      {t_construct - t3:.4f}s")
print(f"  read_csv 合计:      {t_construct - t1:.4f}s")
print(f"apply(type):       {t_apply - t4:.4f}s")
print(f"value_counts:      {t_vc - t5:.4f}s")
print(f"apply+vc 合计:      {t_vc - t4:.4f}s")
print()
print("dtype_str:", s._dtype_str)
print("vc 结果前2行:")
print(vc.head(2))