"""测试 apply(type) 短路优化 - 对比纯类型列和混合列"""
import time
import veloxframe as pd

# 1. 纯 int64 列 - apply(type) 短路优化
s_int = pd.Series(list(range(1000000)), name="x")
t0 = time.time()
r1 = s_int.apply(type)
t1 = time.time()
print(f"int64 apply(type): {t1 - t0:.4f}s")
print(f"  结果 sample: {r1.iloc[0]}")

# 2. int64 apply(type).value_counts()
t0 = time.time()
r2 = s_int.apply(type).value_counts()
t1 = time.time()
print(f"int64 apply(type).value_counts(): {t1 - t0:.4f}s")
print(f"  结果: {r2}")

# 3. 混合列
col_mixed = list(range(500000)) + ["a", "b"] + list(range(500000))
s_mixed = pd.Series(col_mixed, name="x")
t0 = time.time()
r3 = s_mixed.apply(type)
t1 = time.time()
print(f"\nmixed apply(type): {t1 - t0:.4f}s")

t0 = time.time()
r4 = s_mixed.apply(type).value_counts()
t1 = time.time()
print(f"mixed apply(type).value_counts(): {t1 - t0:.4f}s")
print(f"  结果: {r4}")