"""使用 cProfile 剖析 testing_rspandas2.py L773-778 的耗时分布"""
import cProfile
import pstats
import io
import rspandas as pd


def workload():
    col_1 = list(range(500000)) + ["a", "b"] + list(range(500000))
    df = pd.DataFrame({"col_1": col_1})
    df.to_csv("./testing/foo.csv")
    mixed_df = pd.read_csv("./testing/foo.csv")
    mixed_df["col_1"].apply(type).value_counts()


pr = cProfile.Profile()
pr.enable()
workload()
pr.disable()

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
ps.print_stats(40)
print(s.getvalue())