"""验证新一批下沉到 Rust 的方法：argmax/argmin/skew/kurt/mad/autocorr/pct_change/argsort/prod。

对每个方法执行：
1. 正确性测试：与 Python 实现（或 pandas 行为）对比
2. 性能测试：Rust 路径 vs Python 回退路径的加速比

运行：.venv/bin/python debug/verify_argmax_skew_pct_change.py
"""

from __future__ import annotations

import math
import random
import time
from typing import Any

import rspandas as pd
from rspandas import Series


def _measure(fn, label: str, repeats: int = 3) -> float:
    """重复执行 fn 取最小耗时（毫秒）。"""
    best = float("inf")
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        dt = (t1 - t0) * 1000.0
        if dt < best:
            best = dt
    print(f"  {label:50s} → {best:8.3f} ms")
    return best


def _make_int_series(n: int, seed: int = 42) -> Series:
    random.seed(seed)
    return Series([random.randint(-1000, 1000) for _ in range(n)], name="x", dtype="int64")


def _make_float_series(n: int, seed: int = 7) -> Series:
    random.seed(seed)
    return Series([random.uniform(-100.0, 100.0) for _ in range(n)], name="x", dtype="float64")


def _make_int_with_none(n: int, none_ratio: float = 0.1, seed: int = 99) -> Series:
    random.seed(seed)
    vals = [random.randint(0, 1000) for _ in range(n)]
    for i in range(n):
        if random.random() < none_ratio:
            vals[i] = None
    return Series(vals, name="x", dtype="int64")


def _py_argmax(values: list) -> int | None:
    non_null_indices = [i for i, v in enumerate(values) if v is not None]
    if not non_null_indices:
        return None
    return max(non_null_indices, key=lambda i: values[i])


def _py_argmin(values: list) -> int | None:
    non_null_indices = [i for i, v in enumerate(values) if v is not None]
    if not non_null_indices:
        return None
    return min(non_null_indices, key=lambda i: values[i])


def _py_skew(values: list, bias: bool = True) -> float | None:
    non_null = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    n = len(non_null)
    if n < 3:
        return None
    m = sum(non_null) / n
    var = sum((x - m) ** 2 for x in non_null) / n
    if var == 0:
        return 0.0
    std = var ** 0.5
    g = sum((x - m) ** 3 for x in non_null) / (n * std ** 3)
    if not bias:
        g *= (n * (n - 1)) ** 0.5 / (n - 2)
    return g


def _py_mad(values: list) -> float | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    m = sum(vals) / len(vals)
    return sum(abs(x - m) for x in vals) / len(vals)


def _py_pct_change(values: list, periods: int = 1) -> list:
    n = len(values)
    if periods == 0 or abs(periods) >= n:
        return [None] * n
    if periods > 0:
        cur = values[periods:]
        prev = values[: n - periods]
        pad = [None] * periods
    else:
        cur = values[: n + periods]
        prev = values[-periods:]
        pad = [None] * (-periods)
    body = [None if a is None or b is None or b == 0 else (a - b) / b for a, b in zip(cur, prev)]
    return pad + body if periods > 0 else body + pad


def _py_argsort(values: list, ascending: bool = True) -> list:
    indexed = list(enumerate(values))
    non_none = [(i, v) for i, v in indexed if v is not None]
    none_items = [(i, v) for i, v in indexed if v is None]
    non_none.sort(key=lambda x: x[1], reverse=not ascending)
    return [i for i, _ in non_none + none_items]


def _py_prod(values: list) -> Any:
    non_null = [v for v in values if v is not None]
    if not non_null:
        return 1
    result = 1
    for v in non_null:
        result *= v
    return result


# ============================================================
# 正确性测试
# ============================================================


def test_argmax_correctness():
    print("\n=== argmax/argmin 正确性 ===")
    # Int 系列
    s = Series([3, 1, 4, 1, 5, 9, 2, 6], name="x", dtype="int64")
    assert s.argmax() == 5, f"argmax 应为 5 (值 9), got {s.argmax()}"
    assert s.argmin() == 1, f"argmin 应为 1 (首个值 1), got {s.argmin()}"
    assert s.idxmax() == 5
    assert s.idxmin() == 1
    print("  Int64 ✓")

    # Float 系列（含 NaN）
    s_f = Series([1.5, float("nan"), 3.0, 2.0, None], name="x", dtype="float64")
    assert s_f.argmax() == 2, f"argmax 应为 2 (值 3.0), got {s_f.argmax()}"
    assert s_f.argmin() == 0, f"argmin 应为 0 (值 1.5), got {s_f.argmin()}"
    print("  Float64 + NaN ✓")

    # Bool 系列
    s_b = Series([False, True, False, True], name="x", dtype="bool")
    assert s_b.argmax() == 1, f"bool argmax 应为 1 (首个 true), got {s_b.argmax()}"
    assert s_b.argmin() == 0, f"bool argmin 应为 0 (首个 false), got {s_b.argmin()}"
    print("  Bool ✓")

    # String 系列
    s_s = Series(["banana", "apple", "cherry"], name="x", dtype="object")
    assert s_s.argmax() == 2, f"str argmax 应为 2 (cherry), got {s_s.argmax()}"
    assert s_s.argmin() == 1, f"str argmin 应为 1 (apple), got {s_s.argmin()}"
    print("  String ✓")

    # 全 None
    s_n = Series([None, None, None], name="x", dtype="int64")
    assert s_n.argmax() is None
    assert s_n.argmin() is None
    print("  All-None ✓")


def test_skew_kurt_correctness():
    print("\n=== skew/kurt 正确性 ===")
    # 对称分布 → 偏度 ≈ 0
    s = Series([1.0, 2.0, 3.0, 4.0, 5.0], name="x", dtype="float64")
    sk = s.skew()
    assert abs(sk) < 1e-9, f"对称分布 skew 应≈0, got {sk}"
    print(f"  对称分布 skew={sk:.6f} ✓")

    # 偏右分布 → 偏度 > 0
    s_right = Series([1.0, 1.0, 1.0, 1.0, 100.0], name="x", dtype="float64")
    sk_r = s_right.skew()
    assert sk_r > 0, f"右偏分布 skew 应>0, got {sk_r}"
    print(f"  右偏分布 skew={sk_r:.6f} ✓")

    # kurt 对比 Fisher vs Pearson
    s_k = Series([float(i) for i in range(1, 21)], name="x", dtype="float64")
    f = s_k.kurt(bias=True, fisher=True)
    p = s_k.kurt(bias=True, fisher=False)
    assert abs((p - f) - 3.0) < 1e-9, f"Pearson - Fisher 应为 3, got {p - f}"
    print(f"  Fisher={f:.6f}, Pearson={p:.6f}, 差={p - f:.6f} ✓")

    # n < 3 → None
    s_short = Series([1.0, 2.0], name="x", dtype="float64")
    assert s_short.skew() is None
    assert s_short.kurt() is None
    print("  n<3/n<4 → None ✓")


def test_mad_correctness():
    print("\n=== mad 正确性 ===")
    s = Series([1, 2, 3, 4, 5], name="x", dtype="int64")
    # mean=3, |x-3| = 2,1,0,1,2; 平均=6/5=1.2
    assert abs(s.mad() - 1.2) < 1e-9, f"mad 应为 1.2, got {s.mad()}"
    print(f"  Int64 mad={s.mad():.6f} ✓")

    s_f = Series([1.5, 2.5, 3.5], name="x", dtype="float64")
    # mean=2.5, |x-2.5|=1,0,1; 平均=2/3
    assert abs(s_f.mad() - 2.0 / 3.0) < 1e-9, f"float mad 应为 2/3, got {s_f.mad()}"
    print(f"  Float64 mad={s_f.mad():.6f} ✓")


def test_autocorr_correctness():
    print("\n=== autocorr 正确性 ===")
    # lag=0 时相关系数=1
    s = Series(list(range(1, 11)), name="x", dtype="int64")
    v = s.autocorr(0)
    assert abs(v - 1.0) < 1e-9, f"autocorr(0) 应=1.0, got {v}"
    print(f"  lag=0 autocorr={v:.6f} ✓")

    # lag >= n → None
    assert s.autocorr(20) is None
    print("  lag>=n → None ✓")

    # 单调序列 lag=1 应为接近 1
    v1 = s.autocorr(1)
    assert v1 > 0.99, f"单调序列 autocorr(1) 应>0.99, got {v1}"
    print(f"  单调序列 lag=1 autocorr={v1:.6f} ✓")


def test_pct_change_correctness():
    print("\n=== pct_change 正确性 ===")
    # 正 periods
    s = Series([100, 110, 121, 133.1], name="x", dtype="float64")
    r = s.pct_change(1)
    expected = [None, 0.1, 0.1, 0.1]
    for i, (a, e) in enumerate(zip(r.values, expected)):
        if e is None:
            assert a is None, f"位置 {i} 应为 None, got {a}"
        else:
            assert abs(a - e) < 1e-6, f"位置 {i} 期望 {e}, got {a}"
    print(f"  periods=1: {r.values} ✓")

    # 负 periods: 与未来值比较
    # [100, 110, 121, 133.1]
    # i=0: (100-110)/110 = -0.0909...
    # i=1: (110-121)/121 = -0.0909...
    # i=2: (121-133.1)/133.1 = -0.0909...
    # i=3: None
    r_neg = s.pct_change(-1)
    expected_neg = [(100 - 110) / 110, (110 - 121) / 121, (121 - 133.1) / 133.1, None]
    for i, (a, e) in enumerate(zip(r_neg.values, expected_neg)):
        if e is None:
            assert a is None, f"位置 {i} 应为 None, got {a}"
        else:
            assert abs(a - e) < 1e-6, f"位置 {i} 期望 {e}, got {a}"
    print(f"  periods=-1: {r_neg.values} ✓")

    # periods=0 → 全 0.0
    r0 = s.pct_change(0)
    print(f"  periods=0 values: {r0.values}")
    for i, v in enumerate(r0.values):
        if v is None:
            assert False, f"位置 {i} 不应为 None"
        assert v == 0.0 or (isinstance(v, float) and abs(v) < 1e-9), f"位置 {i} 应为 0.0, got {v!r}"
    print("  periods=0 → 全 0.0 ✓")

    # 前值为 0 → None
    s_zero = Series([0, 5, 10], name="x", dtype="int64")
    r_zero = s_zero.pct_change(1)
    assert r_zero.values[0] is None
    assert r_zero.values[1] is None  # 前值为 0
    assert r_zero.values[2] == 1.0  # (10-5)/5
    print(f"  前值为 0: {r_zero.values} ✓")


def test_argsort_correctness():
    print("\n=== argsort 正确性 ===")
    s = Series([30, 10, 20, 10], name="x", dtype="int64")
    asc = list(s.argsort(ascending=True).values)
    assert asc == [1, 3, 2, 0], f"升序应为 [1,3,2,0], got {asc}"
    print(f"  升序: {asc} ✓")

    desc = list(s.argsort(ascending=False).values)
    assert desc == [0, 2, 1, 3], f"降序应为 [0,2,1,3], got {desc}"
    print(f"  降序: {desc} ✓")

    # 含 None
    s_n = Series([3, None, 1, 2, None], name="x", dtype="int64")
    asc_n = list(s_n.argsort(ascending=True).values)
    # 1 (idx=2), 2 (idx=3), 3 (idx=0), None(idx=1), None(idx=4)
    assert asc_n == [2, 3, 0, 1, 4], f"含 None 升序应为 [2,3,0,1,4], got {asc_n}"
    print(f"  含 None 升序: {asc_n} ✓")


def test_prod_correctness():
    print("\n=== prod 正确性 ===")
    s = Series([1, 2, 3, 4, 5], name="x", dtype="int64")
    assert s.prod() == 120, f"prod 应为 120, got {s.prod()}"
    print(f"  Int64 prod={s.prod()} ✓")

    s_f = Series([2.0, 3.0, 4.0], name="x", dtype="float64")
    assert abs(s_f.prod() - 24.0) < 1e-9, f"float prod 应为 24, got {s_f.prod()}"
    print(f"  Float64 prod={s_f.prod()} ✓")

    # 含 NaN
    s_nan = Series([2.0, float("nan"), 3.0], name="x", dtype="float64")
    assert abs(s_nan.prod() - 6.0) < 1e-9, f"含 NaN 应为 6, got {s_nan.prod()}"
    print(f"  含 NaN prod={s_nan.prod()} ✓")


# ============================================================
# 性能测试
# ============================================================


def test_argmax_performance():
    print("\n=== argmax 性能 (500k 整数) ===")
    s = _make_int_series(500_000)
    vals = s.values
    t_rust = _measure(lambda: s.argmax(), "Rust argmax")
    t_py = _measure(lambda: _py_argmax(vals), "Python argmax")
    print(f"  加速比: {t_py / t_rust:.2f}x")

    print("\n=== argmin 性能 (500k 整数) ===")
    t_rust = _measure(lambda: s.argmin(), "Rust argmin")
    t_py = _measure(lambda: _py_argmin(vals), "Python argmin")
    print(f"  加速比: {t_py / t_rust:.2f}x")


def test_skew_performance():
    print("\n=== skew 性能 (100k 浮点) ===")
    s = _make_float_series(100_000)
    vals = s.values
    t_rust = _measure(lambda: s.skew(), "Rust skew", repeats=5)
    t_py = _measure(lambda: _py_skew(vals), "Python skew", repeats=2)
    print(f"  加速比: {t_py / t_rust:.2f}x")


def test_mad_performance():
    print("\n=== mad 性能 (500k 整数) ===")
    s = _make_int_series(500_000)
    vals = s.values
    t_rust = _measure(lambda: s.mad(), "Rust mad")
    t_py = _measure(lambda: _py_mad(vals), "Python mad")
    print(f"  加速比: {t_py / t_rust:.2f}x")


def test_pct_change_performance():
    print("\n=== pct_change 性能 (500k 整数) ===")
    s = _make_int_series(500_000)
    vals = s.values
    t_rust = _measure(lambda: s.pct_change(1), "Rust pct_change")
    t_py = _measure(lambda: _py_pct_change(vals, 1), "Python pct_change", repeats=2)
    print(f"  加速比: {t_py / t_rust:.2f}x")


def test_argsort_performance():
    print("\n=== argsort 性能 (100k 整数) ===")
    s = _make_int_series(100_000)
    vals = s.values
    t_rust = _measure(lambda: s.argsort(True), "Rust argsort")
    t_py = _measure(lambda: _py_argsort(vals, True), "Python argsort", repeats=2)
    print(f"  加速比: {t_py / t_rust:.2f}x")


def test_prod_performance():
    print("\n=== prod 性能 (500k 整数) ===")
    s = _make_int_series(500_000)
    vals = s.values
    t_rust = _measure(lambda: s.prod(), "Rust prod")
    t_py = _measure(lambda: _py_prod(vals), "Python prod")
    print(f"  加速比: {t_py / t_rust:.2f}x")


def test_autocorr_performance():
    print("\n=== autocorr 性能 (100k 整数, lag=1) ===")
    s = _make_int_series(100_000)
    t_rust = _measure(lambda: s.autocorr(1), "Rust autocorr", repeats=5)

    # Python 回退实现
    def _py_autocorr(values, lag):
        vals = [v for v in values if v is not None]
        n = len(vals)
        if n <= lag:
            return None
        s1 = vals[: n - lag]
        s2 = vals[lag:]
        m1 = sum(s1) / len(s1)
        m2 = sum(s2) / len(s2)
        num = sum((a - m1) * (b - m2) for a, b in zip(s1, s2))
        den1 = sum((a - m1) ** 2 for a in s1) ** 0.5
        den2 = sum((b - m2) ** 2 for b in s2) ** 0.5
        if den1 == 0 or den2 == 0:
            return None
        return num / (den1 * den2)

    vals = s.values
    t_py = _measure(lambda: _py_autocorr(vals, 1), "Python autocorr", repeats=2)
    print(f"  加速比: {t_py / t_rust:.2f}x")


def main():
    print("=" * 60)
    print("rspandas 新一批 Rust 加速方法验证")
    print("=" * 60)

    test_argmax_correctness()
    test_skew_kurt_correctness()
    test_mad_correctness()
    test_autocorr_correctness()
    test_pct_change_correctness()
    test_argsort_correctness()
    test_prod_correctness()

    test_argmax_performance()
    test_skew_performance()
    test_mad_performance()
    test_pct_change_performance()
    test_argsort_performance()
    test_prod_performance()
    test_autocorr_performance()

    print("\n" + "=" * 60)
    print("全部测试通过 ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
