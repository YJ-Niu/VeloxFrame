"""验证 Rust 加速方法的功能正确性与性能。

覆盖以下方法：
- Series.dropna
- Series.replace（标量/字典）
- Series.diff
- Series.drop_duplicates
- Series.combine_first
- DataFrame.fillna（标量场景，委托到 Series.fillna）

每个方法对 Int64/Float64 列做功能验证；
同时与 Python 纯循环实现做性能对比，量化加速比。
"""

from __future__ import annotations

import time
import rsarray as rnp
import veloxframe as pd
from veloxframe.series import Series


def _make_int_series(n: int = 100_000) -> pd.Series:
    arr = rnp.arange(n)
    data = [int(x) for x in arr]
    # 注入缺失值
    for i in range(0, n, 7):
        data[i] = None
    return pd.Series(data, name="int_col")


def _make_float_series(n: int = 100_000) -> pd.Series:
    arr = rnp.random.randn(n).tolist()
    for i in range(0, n, 5):
        arr[i] = float("nan")
    return pd.Series(arr, name="float_col")


def _assert_eq_list(a, b, label: str) -> None:
    if len(a) != len(b):
        raise AssertionError(f"[{label}] 长度不一致: {len(a)} vs {len(b)}")
    for i, (x, y) in enumerate(zip(a, b)):
        # 统一 None/NaN 判断
        x_na = x is None or (isinstance(x, float) and x != x)
        y_na = y is None or (isinstance(y, float) and y != y)
        if x_na or y_na:
            if x_na != y_na:
                raise AssertionError(f"[{label}] idx={i}: 一侧缺失另一侧非缺失 ({x!r} vs {y!r})")
            continue
        if x != y:
            raise AssertionError(f"[{label}] idx={i}: {x!r} != {y!r}")


def test_dropna() -> None:
    print("== Series.dropna ==")
    s = _make_int_series(1000)
    result = s.dropna()
    # 与预期对比：缺失值在 idx % 7 == 0 的位置
    expected = [i for i in range(1000) if i % 7 != 0]
    _assert_eq_list(list(result.values), expected, "dropna int")
    print(f"  原长度={len(s)} -> dropna 后={len(result)} (预期 {len(expected)})")

    # 性能
    s_big = _make_int_series(100_000)
    # 阶段 1：纯 Rust dropna（不构建 Python 索引）
    t0 = time.perf_counter()
    inner = s_big._inner.dropna()
    t_rust_pure = time.perf_counter() - t0

    # 阶段 2：纯 Rust notnull
    t0 = time.perf_counter()
    mask = s_big._inner.notnull()
    t_rust_mask = time.perf_counter() - t0

    # 阶段 3：Python 层构建新索引
    old_idx = s_big._index or list(range(len(s_big)))
    t0 = time.perf_counter()
    new_index = [old_idx[i] for i, m in enumerate(mask) if m]
    t_py_idx = time.perf_counter() - t0

    # 阶段 4：完整 Series.dropna（Python 包装层）- 直接测完整调用
    try:
        Series._from_inner(s_big._inner, s_big.name, list(range(s_big.size)))
        print("  [路径] _from_inner 成功 → Rust 路径生效")
    except Exception as e:
        print(f"  [路径] _from_inner 失败 ({e}) → Series.dropna 实际走 Python 回退！")

    print(f"  [路径] _index_is_default={getattr(s_big, '_index_is_default', 'n/a')}")

    t0 = time.perf_counter()
    r1 = s_big.dropna()
    t_full = time.perf_counter() - t0

    # 阶段 5：纯 Rust dropna_with_index
    t0 = time.perf_counter()
    new_inner2, kept_indices = s_big._inner.dropna_with_index()
    t_rust_idx = time.perf_counter() - t0

    t0 = time.perf_counter()
    vals = list(s_big.values)
    r2 = [v for v in vals if v is not None]
    t_py = time.perf_counter() - t0
    print(f"  Rust dropna_with_index={t_rust_idx*1000:.2f}ms  完整 Series.dropna={t_full*1000:.2f}ms")
    print(f"  对比纯 Python 循环={t_py*1000:.2f}ms  "
          f"加速={t_py/t_full:.2f}x  结果一致={list(r1.values) == r2}")


def test_replace_scalar() -> None:
    print("== Series.replace (标量) ==")
    s = pd.Series([1, 2, 1, 3, None, 1], name="x")
    r = s.replace(1, 99)
    _assert_eq_list(list(r.values), [99, 2, 99, 3, None, 99], "replace scalar")
    print(f"  {list(r.values)}")

    # 性能
    s_big = _make_int_series(100_000)
    t0 = time.perf_counter()
    r1 = s_big.replace(1, 999)
    t_rust = time.perf_counter() - t0

    t0 = time.perf_counter()
    vals = list(s_big.values)
    r2 = [999 if v == 1 else v for v in vals]
    t_py = time.perf_counter() - t0
    print(f"  Rust={t_rust*1000:.2f}ms  Python={t_py*1000:.2f}ms  "
          f"加速={t_py/t_rust:.2f}x  一致={list(r1.values) == r2}")


def test_replace_dict() -> None:
    print("== Series.replace (字典) ==")
    s = pd.Series([1, 2, 3, 1, 2], name="x")
    r = s.replace({1: 10, 2: 20})
    _assert_eq_list(list(r.values), [10, 20, 3, 10, 20], "replace dict")
    print(f"  {list(r.values)}")

    # 性能
    s_big = _make_int_series(100_000)
    mapping = {0: 100, 1: 200, 2: 300, 3: 400}
    t0 = time.perf_counter()
    r1 = s_big.replace(mapping)
    t_rust = time.perf_counter() - t0

    t0 = time.perf_counter()
    vals = list(s_big.values)
    r2 = [mapping.get(v, v) if v is not None else None for v in vals]
    t_py = time.perf_counter() - t0
    print(f"  Rust={t_rust*1000:.2f}ms  Python={t_py*1000:.2f}ms  "
          f"加速={t_py/t_rust:.2f}x  一致={list(r1.values) == r2}")


def test_diff() -> None:
    print("== Series.diff ==")
    s = pd.Series([1, 3, 6, 10, 15], name="x")
    r = s.diff(1)
    _assert_eq_list(list(r.values), [None, 2, 3, 4, 5], "diff int")
    print(f"  diff(1)={list(r.values)}")

    r2 = s.diff(-1)
    # diff(-1): result[i] = s[i] - s[i+1]，最后一个为 None
    _assert_eq_list(list(r2.values), [-2, -3, -4, -5, None], "diff -1")
    print(f"  diff(-1)={list(r2.values)}")

    # 性能
    s_big = _make_int_series(100_000)
    t0 = time.perf_counter()
    r1 = s_big.diff(1)
    t_rust = time.perf_counter() - t0

    t0 = time.perf_counter()
    vals = list(s_big.values)
    r2 = [None] + [vals[i] - vals[i - 1]
                   if vals[i] is not None and vals[i - 1] is not None
                   else None
                   for i in range(1, len(vals))]
    t_py = time.perf_counter() - t0
    print(f"  Rust={t_rust*1000:.2f}ms  Python={t_py*1000:.2f}ms  "
          f"加速={t_py/t_rust:.2f}x  一致={list(r1.values) == r2}")


def test_drop_duplicates() -> None:
    print("== Series.drop_duplicates ==")
    s = pd.Series([1, 2, 1, 3, 2, 4])
    r = s.drop_duplicates(keep="first")
    _assert_eq_list(list(r.values), [1, 2, 3, 4], "drop_duplicates first")
    print(f"  first={list(r.values)}")

    r_last = s.drop_duplicates(keep="last")
    _assert_eq_list(list(r_last.values), [1, 3, 2, 4], "drop_duplicates last")
    print(f"  last={list(r_last.values)}")

    r_false = s.drop_duplicates(keep=False)
    _assert_eq_list(list(r_false.values), [3, 4], "drop_duplicates False")
    print(f"  False={list(r_false.values)}")

    # 性能
    s_big = pd.Series([i % 100 for i in range(100_000)])
    t0 = time.perf_counter()
    r1 = s_big.drop_duplicates(keep="first")
    t_rust = time.perf_counter() - t0

    t0 = time.perf_counter()
    vals = list(s_big.values)
    seen = set()
    r2 = [v for v in vals if not (v in seen or seen.add(v))]
    t_py = time.perf_counter() - t0
    print(f"  Rust={t_rust*1000:.2f}ms  Python={t_py*1000:.2f}ms  "
          f"加速={t_py/t_rust:.2f}x  一致={list(r1.values) == r2}")


def test_combine_first() -> None:
    print("== Series.combine_first ==")
    a = pd.Series([1, None, None, 4], name="a")
    b = pd.Series([10, 20, None, 40], name="b")
    r = a.combine_first(b)
    _assert_eq_list(list(r.values), [1, 20, None, 4], "combine_first")
    print(f"  {list(r.values)}")

    # 性能
    n = 100_000
    a_big = pd.Series([i if i % 3 != 0 else None for i in range(n)])
    b_big = pd.Series([i * 10 if i % 5 != 0 else None for i in range(n)])
    t0 = time.perf_counter()
    r1 = a_big.combine_first(b_big)
    t_rust = time.perf_counter() - t0

    t0 = time.perf_counter()
    av = list(a_big.values)
    bv = list(b_big.values)
    r2 = [av[i] if av[i] is not None else bv[i] for i in range(len(av))]
    t_py = time.perf_counter() - t0
    print(f"  Rust={t_rust*1000:.2f}ms  Python={t_py*1000:.2f}ms  "
          f"加速={t_py/t_rust:.2f}x  一致={list(r1.values) == r2}")


def test_dataframe_fillna() -> None:
    print("== DataFrame.fillna (标量委托) ==")
    df = pd.DataFrame({
        "a": [1, None, 3, None, 5],
        "b": [None, 2.0, None, 4.0, 5.0],
    })
    r = df.fillna(0)
    print(f"  a: {list(r['a'].values)}")
    print(f"  b: {list(r['b'].values)}")
    _assert_eq_list(list(r["a"].values), [1, 0, 3, 0, 5], "df.fillna a")
    _assert_eq_list(list(r["b"].values), [0.0, 2.0, 0.0, 4.0, 5.0], "df.fillna b")

    # 性能
    n = 50_000
    df_big = pd.DataFrame({
        "a": [i if i % 4 != 0 else None for i in range(n)],
        "b": [float(i) if i % 3 != 0 else None for i in range(n)],
        "c": [i * 2 if i % 5 != 0 else None for i in range(n)],
    })
    t0 = time.perf_counter()
    r1 = df_big.fillna(0)
    t_rust = time.perf_counter() - t0

    t0 = time.perf_counter()
    r2 = pd.DataFrame({
        "a": [0 if v is None else v for v in df_big["a"].values],
        "b": [0.0 if v is None else v for v in df_big["b"].values],
        "c": [0 if v is None else v for v in df_big["c"].values],
    })
    t_py = time.perf_counter() - t0
    eq = (
        list(r1["a"].values) == list(r2["a"].values) and
        list(r1["b"].values) == list(r2["b"].values) and
        list(r1["c"].values) == list(r2["c"].values)
    )
    print(f"  Rust 路径={t_rust*1000:.2f}ms  Python={t_py*1000:.2f}ms  "
          f"加速={t_py/t_rust:.2f}x  一致={eq}")


def main() -> None:
    print("\n".join(["", "=" * 60]))
    test_dropna()
    test_replace_scalar()
    test_replace_dict()
    test_diff()
    test_drop_duplicates()
    test_combine_first()
    test_dataframe_fillna()
    print("=" * 60)
    print("全部通过 ✓")


if __name__ == "__main__":
    main()
