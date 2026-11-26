"""验证 Rust 加速的 astype / isin / between / abs / clip / round / cumsum / cumprod / cummax / cummin / shift。

测试维度：
1. 功能正确性：与 Python 回退路径结果对比
2. 性能：Rust 路径 vs Python 路径的加速比
"""

from __future__ import annotations

import random
import time
from typing import Callable

import rspandas as rp
from rspandas import Series

random.seed(42)


def _make_int_series(n: int = 100_000) -> Series:
    """构造 int64 Series，包含 5% None。"""
    data = [
        None if random.random() < 0.05 else random.randint(-1000, 1000)
        for _ in range(n)
    ]
    return Series(data, name="x", dtype="int64")


def _make_float_series(n: int = 100_000) -> Series:
    """构造 float64 Series，包含 5% None。"""
    data = [
        None if random.random() < 0.05 else random.uniform(-100, 100) for _ in range(n)
    ]
    return Series(data, name="x", dtype="float64")


def _make_string_series(n: int = 10_000) -> Series:
    """构造 string Series，包含 5% None。"""
    pool = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
    data = [None if random.random() < 0.05 else random.choice(pool) for _ in range(n)]
    return Series(data, name="x", dtype="object")


def _make_bool_series(n: int = 50_000) -> Series:
    """构造 bool Series，包含 5% None。"""
    data = [
        None if random.random() < 0.05 else random.choice([True, False])
        for _ in range(n)
    ]
    return Series(data, name="x", dtype="bool")


def _measure(fn: Callable, label: str, repeat: int = 3) -> float:
    """测量函数多次执行的最小耗时（ms）。"""
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        elapsed = (time.perf_counter() - t0) * 1000
        best = min(best, elapsed)
    print(f"  {label:30s} {best:8.2f} ms")
    return best


def _check_equal(actual: Series, expected: Series, label: str) -> None:
    """断言两个 Series 的值列表一致。"""
    a = list(actual.values)
    e = list(expected.values)
    if a == e:
        print(f"  [OK] {label}")
        return
    # 浮点近似比较（仅当两边都是数值）
    if len(a) == len(e):
        all_close = True
        for x, y in zip(a, e):
            if x is None or y is None:
                if x is not y:
                    all_close = False
                    break
            elif (
                isinstance(x, (int, float))
                and isinstance(y, (int, float))
                and not isinstance(x, bool)
                and not isinstance(y, bool)
            ):
                if abs(x - y) > 1e-9:
                    all_close = False
                    break
            else:
                if x != y:
                    all_close = False
                    break
        if all_close:
            print(f"  [OK] {label} (数值近似相等)")
            return
    print(f"  [FAIL] {label}")
    print(f"    actual[:5]={a[:5]}")
    print(f"    expected[:5]={e[:5]}")
    diff_idx = next((i for i, (x, y) in enumerate(zip(a, e)) if x != y), None)
    if diff_idx is not None:
        print(
            f"    第一个差异位置 idx={diff_idx}: actual={a[diff_idx]} expected={e[diff_idx]}"
        )


# ============================================================
# astype 测试
# ============================================================
def test_astype_correctness() -> None:
    print("\n=== astype 正确性 ===")

    # int -> float64
    s = Series([1, 2, None, 4, -5], name="x", dtype="int64")
    _check_equal(
        s.astype("float64"),
        Series([1.0, 2.0, None, 4.0, -5.0], name="x", dtype="float64"),
        "int->float64",
    )

    # float64 -> str
    s = Series([1.5, 2.0, None, 3.7], name="x", dtype="float64")
    result = s.astype("str")
    expected_vals = [None if v is None else str(v) for v in s.values]
    _check_equal(result, Series(expected_vals, name="x", dtype="object"), "float->str")

    # int -> bool
    s = Series([0, 1, 5, None, -3], name="x", dtype="int64")
    _check_equal(
        s.astype("bool"),
        Series([False, True, True, None, True], name="x", dtype="bool"),
        "int->bool",
    )

    # int -> int32 (同族)
    s = Series([1, 2, 3], name="x", dtype="int64")
    r = s.astype("int32")
    assert r._dtype_str == "int32", f"dtype 应保持 int32，实际 {r._dtype_str}"
    print(f"  [OK] int64->int32 子类型保留 (dtype_str={r._dtype_str})")

    # uint8 子类型
    r = s.astype("uint8")
    assert r._dtype_str == "uint8", f"dtype 应为 uint8，实际 {r._dtype_str}"
    print(f"  [OK] int64->uint8 子类型保留 (dtype_str={r._dtype_str})")


def test_astype_performance() -> None:
    print("\n=== astype 性能 ===")
    s_int = _make_int_series(500_000)
    s_float = _make_float_series(500_000)

    # Rust 路径：int -> float64
    t_rust = _measure(lambda: s_int.astype("float64"), "Rust: int->float64")

    # 对比：强制走 Python 路径
    def _python_int_to_float():
        vals = [None if v is None else float(v) for v in s_int.values]
        return Series(vals, name="x", dtype="float64")

    t_py = _measure(_python_int_to_float, "Python: int->float64")
    print(f"  加速比: {t_py / t_rust:.2f}x")

    # Rust 路径：float -> str
    t_rust2 = _measure(lambda: s_float.astype("str"), "Rust: float->str")

    def _python_float_to_str():
        vals = [None if v is None else str(v) for v in s_float.values]
        return Series(vals, name="x", dtype="object")

    t_py2 = _measure(_python_float_to_str, "Python: float->str")
    print(f"  加速比: {t_py2 / t_rust2:.2f}x")


# ============================================================
# isin 测试
# ============================================================
def test_isin_correctness() -> None:
    print("\n=== isin 正确性 ===")

    # int 列
    s = Series([1, 2, 3, None, 5], name="x", dtype="int64")
    expected = Series([True, False, True, False, False], name="x", dtype="bool")
    _check_equal(s.isin([1, 3]), expected, "int isin [1,3]")

    # float 列
    s = Series([1.5, 2.5, 3.5, None], name="x", dtype="float64")
    expected = Series([True, False, True, False], name="x", dtype="bool")
    _check_equal(s.isin([1.5, 3.5]), expected, "float isin [1.5,3.5]")

    # string 列
    s = Series(["a", "b", "c", None, "a"], name="x", dtype="object")
    expected = Series([True, False, False, False, True], name="x", dtype="bool")
    _check_equal(s.isin(["a", "x"]), expected, "string isin [a,x]")

    # bool 列
    s = Series([True, False, None, True], name="x", dtype="bool")
    expected = Series([True, False, False, True], name="x", dtype="bool")
    _check_equal(s.isin([True]), expected, "bool isin [True]")

    # 混合类型（应回退到 Python）
    s = Series([1, 2, 3], name="x", dtype="int64")
    result = s.isin([1, "a", 2.5])
    expected_vals = [v in {1, "a", 2.5} for v in s.values]
    _check_equal(
        result, Series(expected_vals, name="x", dtype="bool"), "int isin 混合类型"
    )


def test_isin_performance() -> None:
    print("\n=== isin 性能 ===")
    s_int = _make_int_series(500_000)
    other_int = list(range(0, 1000, 3))  # 333 个元素

    t_rust = _measure(lambda: s_int.isin(other_int), "Rust: int isin")

    def _python_isin():
        s = set(other_int)
        out = [v in s for v in s_int.values]
        return Series(out, name="x", dtype="bool")

    t_py = _measure(_python_isin, "Python: int isin")
    print(f"  加速比: {t_py / t_rust:.2f}x")

    # string isin
    s_str = _make_string_series(100_000)
    other_str = ["alpha", "beta", "gamma"]
    t_rust2 = _measure(lambda: s_str.isin(other_str), "Rust: string isin")

    def _python_str_isin():
        s = set(other_str)
        out = [v in s for v in s_str.values]
        return Series(out, name="x", dtype="bool")

    t_py2 = _measure(_python_str_isin, "Python: string isin")
    print(f"  加速比: {t_py2 / t_rust2:.2f}x")


# ============================================================
# between 测试
# ============================================================
def test_between_correctness() -> None:
    print("\n=== between 正确性 ===")
    s = Series([1, 2, 3, 4, 5, None], name="x", dtype="int64")

    _check_equal(
        s.between(2, 4, "both"),
        Series([False, True, True, True, False, False], name="x", dtype="bool"),
        "between both [2,4]",
    )
    _check_equal(
        s.between(2, 4, "left"),
        Series([False, True, True, False, False, False], name="x", dtype="bool"),
        "between left [2,4)",
    )
    _check_equal(
        s.between(2, 4, "neither"),
        Series([False, False, True, False, False, False], name="x", dtype="bool"),
        "between neither (2,4)",
    )


# ============================================================
# abs / clip / round / cumsum / cumprod / cummax / cummin / shift 测试
# ============================================================
def test_numeric_correctness() -> None:
    print("\n=== 数值运算正确性 ===")

    # abs
    s = Series([-1, 2, -3, None, 5], name="x", dtype="int64")
    _check_equal(
        s.abs(), Series([1, 2, 3, None, 5], name="x", dtype="int64"), "abs int"
    )

    s = Series([-1.5, 2.0, None, 3.7], name="x", dtype="float64")
    _check_equal(
        s.abs(), Series([1.5, 2.0, None, 3.7], name="x", dtype="float64"), "abs float"
    )

    # clip
    s = Series([-5, 0, 5, 10, None], name="x", dtype="int64")
    _check_equal(
        s.clip(0, 7),
        Series([0, 0, 5, 7, None], name="x", dtype="int64"),
        "clip int [0,7]",
    )

    # round
    s = Series([1.234, 2.345, 3.456, None], name="x", dtype="float64")
    _check_equal(
        s.round(2),
        Series([1.23, 2.35, 3.46, None], name="x", dtype="float64"),
        "round float 2",
    )

    # cumsum
    s = Series([1, 2, None, 4, 5], name="x", dtype="int64")
    _check_equal(
        s.cumsum(),
        Series([1, 3, 3, 7, 12], name="x", dtype="int64"),
        "cumsum int",
    )

    # 前导 None
    s = Series([None, 1, 2, None, 4], name="x", dtype="int64")
    _check_equal(
        s.cumsum(),
        Series([None, 1, 3, 3, 7], name="x", dtype="int64"),
        "cumsum 前导 None",
    )

    # cumprod
    s = Series([2, 3, None, 4], name="x", dtype="int64")
    _check_equal(
        s.cumprod(),
        Series([2, 6, 6, 24], name="x", dtype="int64"),
        "cumprod int",
    )

    # cummax
    s = Series([3, 1, 5, None, 2], name="x", dtype="int64")
    _check_equal(
        s.cummax(),
        Series([3, 3, 5, 5, 5], name="x", dtype="int64"),
        "cummax int",
    )

    # cummin
    s = Series([3, 1, 5, None, 2], name="x", dtype="int64")
    _check_equal(
        s.cummin(),
        Series([3, 1, 1, 1, 1], name="x", dtype="int64"),
        "cummin int",
    )

    # shift +1
    s = Series([10, 20, 30, 40], name="x", dtype="int64")
    _check_equal(
        s.shift(1),
        Series([None, 10, 20, 30], name="x", dtype="int64"),
        "shift +1",
    )

    # shift -1
    _check_equal(
        s.shift(-1),
        Series([20, 30, 40, None], name="x", dtype="int64"),
        "shift -1",
    )

    # shift 0
    _check_equal(s.shift(0), s, "shift 0")

    # shift 超长
    _check_equal(
        s.shift(100),
        Series([None, None, None, None], name="x", dtype="int64"),
        "shift 100 (全 None)",
    )


def test_numeric_performance() -> None:
    print("\n=== 数值运算性能 (500k 元素) ===")
    s_int = _make_int_series(500_000)
    s_float = _make_float_series(500_000)

    # abs
    t_rust = _measure(lambda: s_int.abs(), "Rust: abs int")
    t_py = _measure(
        lambda: Series(
            [None if v is None else abs(v) for v in s_int.values],
            name="x",
            dtype="int64",
        ),
        "Python: abs int",
    )
    print(f"  加速比: {t_py / t_rust:.2f}x")

    # round
    t_rust = _measure(lambda: s_float.round(2), "Rust: round float")
    t_py = _measure(
        lambda: Series(
            [None if v is None else round(v, 2) for v in s_float.values],
            name="x",
            dtype="float64",
        ),
        "Python: round float",
    )
    print(f"  加速比: {t_py / t_rust:.2f}x")

    # clip
    t_rust = _measure(lambda: s_int.clip(0, 1000), "Rust: clip int")
    t_py = _measure(
        lambda: Series(
            [
                None if v is None else (0 if v < 0 else (1000 if v > 1000 else v))
                for v in s_int.values
            ],
            name="x",
            dtype="int64",
        ),
        "Python: clip int",
    )
    print(f"  加速比: {t_py / t_rust:.2f}x")

    # cumsum
    t_rust = _measure(lambda: s_int.cumsum(), "Rust: cumsum int")
    t_py = _measure(
        lambda: _py_cumsum(s_int),
        "Python: cumsum int",
    )
    print(f"  加速比: {t_py / t_rust:.2f}x")

    # shift
    t_rust = _measure(lambda: s_int.shift(1), "Rust: shift int")
    t_py = _measure(lambda: _py_shift(s_int, 1), "Python: shift int")
    print(f"  加速比: {t_py / t_rust:.2f}x")


def _py_cumsum(s: Series) -> Series:
    """Python 实现：skipna=True cumsum。"""
    acc = None
    out = []
    for v in s.values:
        if v is None:
            out.append(acc)
        else:
            acc = v if acc is None else acc + v
            out.append(acc)
    return Series(out, name="x", index=s._index)


def _py_shift(s: Series, periods: int) -> Series:
    """Python 实现：shift。"""
    values = list(s.values)
    n = len(values)
    out: list = [None] * n
    if periods > 0 and periods < n:
        out[periods:] = values[: n - periods]
    elif periods < 0 and -periods < n:
        out[: n + periods] = values[-periods:]
    elif periods == 0:
        out = list(values)
    return Series(out, name="x", index=s._index)


if __name__ == "__main__":
    print(f"rspandas 版本: {rp.__version__}")
    test_astype_correctness()
    test_astype_performance()
    test_isin_correctness()
    test_isin_performance()
    test_between_correctness()
    test_numeric_correctness()
    test_numeric_performance()
    print("\n=== 验证完成 ===")
