"""重新剖析 read_csv 内部耗时分布（优化后）"""
import cProfile
import pstats
import io
import rspandas as pd

col_1 = list(range(500000)) + ["a", "b"] + list(range(500000))
df = pd.DataFrame({"col_1": col_1})
df.to_csv("./testing/foo.csv")


def workload():
    mixed_df = pd.read_csv("./testing/foo.csv")


pr = cProfile.Profile()
pr.enable()
workload()
pr.disable()

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats("tottime")
ps.print_stats(30)
print(s.getvalue())