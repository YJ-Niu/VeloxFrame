"""测试 testing_veloxframe2.py 中 L773-778 的具体性能"""
import time
import veloxframe as pd

# 测试: L773-778
col_1 = list(range(500000)) + ["a", "b"] + list(range(500000))
df = pd.DataFrame({"col_1": col_1})

t0 = time.time()
df.to_csv("./testing/foo.csv")
t_write = time.time()

mixed_df = pd.read_csv("./testing/foo.csv")
t_read = time.time()

result = mixed_df["col_1"].apply(type).value_counts()
t_apply = time.time()

print(f"to_csv: {t_write - t0:.4f}s")
print(f"read_csv: {t_read - t_write:.4f}s")
print(f"apply(type).value_counts(): {t_apply - t_read:.4f}s")
print(f"总耗时: {t_apply - t0:.4f}s")
print(f"结果: {result}")
