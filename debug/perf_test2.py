"""测试 read_csv 路径和 apply(type) 性能"""
import time

import rspandas as pd

# 1. 测试: 直接读取 CSV
col_1 = list(range(500000)) + ["a", "b"] + list(range(500000))
df = pd.DataFrame({"col_1": col_1})
df.to_csv("./debug/foo.csv", index=False)

# 读取 CSV
t0 = time.time()
mixed_df = pd.read_csv("./debug/foo.csv")
t1 = time.time()
print(f"read_csv (no index): {t1 - t0:.4f}s")
print(f"  shape: {mixed_df.shape}")
print(f"  dtypes: {mixed_df.dtypes}")
print(f"  col_1[0]={repr(mixed_df['col_1'].iloc[0])}, type={type(mixed_df['col_1'].iloc[0])}")
print(f"  col_1[500000]={repr(mixed_df['col_1'].iloc[500000])}, type={type(mixed_df['col_1'].iloc[500000])}")

# 2. apply(type).value_counts
t0 = time.time()
vc = mixed_df["col_1"].apply(type).value_counts()
t1 = time.time()
print(f"apply(type).value_counts(): {t1 - t0:.4f}s")
print(f"  结果: {vc}")

# 3. 简化版: 直接 value_counts
t0 = time.time()
vc2 = mixed_df["col_1"].value_counts()
t1 = time.time()
print(f"value_counts(): {t1 - t0:.4f}s")

# 4. 测试: 更大的数据
print("\n--- 更大数据测试 (2M rows) ---")
col_2 = list(range(1000000)) + ["a", "b"] + list(range(1000000))
df2 = pd.DataFrame({"col_1": col_2})
t0 = time.time()
df2.to_csv("./debug/foo2.csv", index=False)
t1 = time.time()
print(f"to_csv: {t1 - t0:.4f}s")

t0 = time.time()
mixed_df2 = pd.read_csv("./debug/foo2.csv")
t1 = time.time()
print(f"read_csv: {t1 - t0:.4f}s")

t0 = time.time()
vc3 = mixed_df2["col_1"].apply(type).value_counts()
t1 = time.time()
print(f"apply(type).value_counts(): {t1 - t0:.4f}s")
print(f"  结果: {vc3}")