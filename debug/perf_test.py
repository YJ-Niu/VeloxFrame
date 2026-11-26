"""测试 read_csv 和 apply(type) 性能"""
import time

import rspandas as pd

# 测试数据
col_1 = list(range(500000)) + ["a", "b"] + list(range(500000))
print(f"数据行数: {len(col_1)}")

# 1. 创建 DataFrame
t0 = time.time()
df = pd.DataFrame({"col_1": col_1})
t1 = time.time()
print(f"DataFrame 创建: {t1 - t0:.4f}s")

# 2. 写入 CSV
t0 = time.time()
df.to_csv("./debug/foo.csv")
t1 = time.time()
print(f"to_csv: {t1 - t0:.4f}s")

# 3. 读取 CSV
t0 = time.time()
mixed_df = pd.read_csv("./debug/foo.csv")
t1 = time.time()
print(f"read_csv: {t1 - t0:.4f}s")
print(f"  mixed_df shape: {mixed_df.shape}")
print(f"  mixed_df dtypes: {mixed_df.dtypes}")

# 4. apply(type)
t0 = time.time()
result = mixed_df["col_1"].apply(type)
t1 = time.time()
print(f"apply(type): {t1 - t0:.4f}s")

# 5. value_counts
t0 = time.time()
vc = result.value_counts()
t1 = time.time()
print(f"value_counts: {t1 - t0:.4f}s")
print(f"结果: {vc}")

# 6. 直接 apply(type).value_counts()
t0 = time.time()
vc2 = mixed_df["col_1"].apply(type).value_counts()
t1 = time.time()
print(f"apply(type).value_counts(): {t1 - t0:.4f}s")
print(f"结果: {vc2}")