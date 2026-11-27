"""测试: 检测 read_csv 的路径"""
import veloxframe as pd
import time

# Patch 来检测路径
import veloxframe.io.csv as csv_mod
orig = csv_mod.read_csv

def patched(*args, **kwargs):
    result = orig(*args, **kwargs)
    print(f"  _col_dtypes: {result._col_dtypes}")
    print(f"  _col_object_values keys: {list(result._col_object_values.keys())}")
    return result

csv_mod.read_csv = patched

col_1 = list(range(500000)) + ["a", "b"] + list(range(500000))
df = pd.DataFrame({"col_1": col_1})
df.to_csv("./debug/foo.csv", index=False)

print("--- read_csv ---")
t0 = time.time()
mixed_df = pd.read_csv("./debug/foo.csv")
t1 = time.time()
print(f"  耗时: {t1 - t0:.4f}s")
print(f"  col_1[0]={repr(mixed_df['col_1'].iloc[0])}, type={type(mixed_df['col_1'].iloc[0])}")

t0 = time.time()
vc = mixed_df["col_1"].apply(type).value_counts()
t1 = time.time()
print(f"apply(type).value_counts(): {t1 - t0:.4f}s")
print(f"  结果: {vc}")