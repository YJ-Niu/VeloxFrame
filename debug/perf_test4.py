"""测试 apply(type) 短路优化效果"""
import time
import rspandas as pd

# 1. 纯 int64 列
s_int = pd.Series(list(range(1000000)), name="x")
t0 = time.time()
r1 = s_int.apply(type)
t1 = time.time()
print(f"int64 apply(type): {t1 - t0:.4f}s")

# 2. 纯 float64 列
s_float = pd.Series([float(i) for i in range(1000000)], name="x")
t0 = time.time()
r2 = s_float.apply(type)
t1 = time.time()
print(f"float64 apply(type): {t1 - t0:.4f}s")

# 3. 纯 str 列
s_str = pd.Series([str(i) for i in range(1000000)], name="x")
t0 = time.time()
r3 = s_str.apply(type)
t1 = time.time()
print(f"str apply(type): {t1 - t0:.4f}s")

# 4. bool 列
s_bool = pd.Series([True, False] * 500000, name="x")
t0 = time.time()
r4 = s_bool.apply(type)
t1 = time.time()
print(f"bool apply(type): {t1 - t0:.4f}s")

# 5. 混合列 (object)
col_mixed = list(range(500000)) + ["a", "b"] + list(range(500000))
s_mixed = pd.Series(col_mixed, name="x")
t0 = time.time()
r5 = s_mixed.apply(type)
t1 = time.time()
print(f"object apply(type): {t1 - t0:.4f}s")

# 6. apply(type).value_counts() 混合列
t0 = time.time()
r6 = s_mixed.apply(type).value_counts()
t1 = time.time()
print(f"object apply(type).value_counts(): {t1 - t0:.4f}s")
print(f"  结果: {r6}")