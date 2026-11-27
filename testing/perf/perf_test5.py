"""测试 read_csv 纯类型列性能"""
import time
import veloxframe as pd

# 1. 纯 int64 列（1M行）
df = pd.DataFrame({"a": list(range(1000000))})
t0 = time.time()
df.to_csv("./debug/pure_int.csv", index=False)
t1 = time.time()
print(f"to_csv (int64, 1M): {t1 - t0:.4f}s")

t0 = time.time()
df2 = pd.read_csv("./debug/pure_int.csv")
t1 = time.time()
print(f"read_csv (int64, 1M): {t1 - t0:.4f}s")
print(f"  dtype: {df2.dtypes['a']}")

# 2. 纯 float64 列（1M行）
df = pd.DataFrame({"a": [float(i) for i in range(1000000)]})
t0 = time.time()
df.to_csv("./debug/pure_float.csv", index=False)
t1 = time.time()
print(f"\nto_csv (float64, 1M): {t1 - t0:.4f}s")

t0 = time.time()
df2 = pd.read_csv("./debug/pure_float.csv")
t1 = time.time()
print(f"read_csv (float64, 1M): {t1 - t0:.4f}s")
print(f"  dtype: {df2.dtypes['a']}")

# 3. 纯 str 列（1M行）
df = pd.DataFrame({"a": [str(i) for i in range(1000000)]})
t0 = time.time()
df.to_csv("./debug/pure_str.csv", index=False)
t1 = time.time()
print(f"\nto_csv (str, 1M): {t1 - t0:.4f}s")

t0 = time.time()
df2 = pd.read_csv("./debug/pure_str.csv")
t1 = time.time()
print(f"read_csv (str, 1M): {t1 - t0:.4f}s")
print(f"  dtype: {df2.dtypes['a']}")

# 4. 混合列（1M+2行）
col = list(range(500000)) + ["a", "b"] + list(range(500000))
df = pd.DataFrame({"col_1": col})
t0 = time.time()
df.to_csv("./debug/mixed.csv", index=False)
t1 = time.time()
print(f"\nto_csv (mixed, 1M+2): {t1 - t0:.4f}s")

t0 = time.time()
df2 = pd.read_csv("./debug/mixed.csv")
t1 = time.time()
print(f"read_csv (mixed, 1M+2): {t1 - t0:.4f}s")
print(f"  dtype: {df2.dtypes['col_1']}")
print(f"  value[0]={repr(df2['col_1'].iloc[0])}, type={type(df2['col_1'].iloc[0])}")

t0 = time.time()
vc = df2["col_1"].apply(type).value_counts()
t1 = time.time()
print(f"apply(type).value_counts(): {t1 - t0:.4f}s")
print(f"  结果: {vc}")