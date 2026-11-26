"""验证 read_csv typed 快速路径的正确性与性能。"""
import os
import time

import rspandas as pd

tmp = os.path.join(os.path.dirname(__file__), "_verify_tmp.csv")

print("=" * 60)
print("1. 小规模混合类型列类型推断正确性")
print("=" * 60)

# 直接写 CSV 文件，走 typed 快速路径
with open(tmp, "w") as f:
    f.write("col_1\n1\n2\n'A'\n4.22\n")

df_a = pd.read_csv(tmp)
print("dtypes:", df_a.dtypes)
print("values:", list(df_a["col_1"].values))
print("apply(type).value_counts():")
print(df_a["col_1"].apply(type).value_counts())
os.remove(tmp)

print()
print("=" * 60)
print("2. 大文件混合类型列性能 + 正确性")
print("=" * 60)

n = 500000
col_1 = list(range(n)) + ["a", "b"] + list(range(n))
df_src = pd.DataFrame({"col_1": col_1})
t0 = time.time()
df_src.to_csv(tmp)
t1 = time.time()
print(f"to_csv: {t1 - t0:.4f}s")

t2 = time.time()
mixed = pd.read_csv(tmp)
t3 = time.time()
print(f"read_csv: {t3 - t2:.4f}s")

t4 = time.time()
vc = mixed["col_1"].apply(type).value_counts()
t5 = time.time()
print(f"apply(type).value_counts(): {t5 - t4:.4f}s")
print(vc)
print("shape:", mixed.shape)
print("dtypes:", mixed.dtypes)

os.remove(tmp)
print("done")