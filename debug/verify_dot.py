"""验证 dot 方法的 Rust 加速。

运行：.venv/bin/python debug/verify_dot.py
"""

from __future__ import annotations

import math
import random
import time
from typing import Any

from rspandas import Series


def _measure(fn, label: str, repeats: int = 3) -> float:
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


def _py_dot(self_vals: list, other_vals: list) -> Any:
    return sum(
        a * b for a, b in zip(self_vals, other_vals) if a is not None and b is not None
    )


def test_dot_correctness():
    print("\n=== dot 正确性 ===")
    # Int * Int
    s = Series([1, 2, 3, 4], name="x", dtype="int64")
    other = Series([10, 20, 30, 40], name="y", dtype="int64")
    r = s.dot(other)
    assert r == 10 + 40 + 90 + 160 == 300, f"int*int 应为 300, got {r}"
    print(f"  int*int: {r} ✓")

    # Int * list
    r2 = s.dot([10, 20, 30, 40])
    assert r2 == 300, f"int*list 应为 300, got {r2}"
    print(f"  int*list: {r2} ✓")

    # Float * Float
    s_f = Series([1.5, 2.5, 3.5], name="x", dtype="float64")
    other_f = Series([2.0, 2.0, 2.0], name="y", dtype="float64")
    r = s_f.dot(other_f)
    expected = 3.0 + 5.0 + 7.0
    assert abs(r - expected) < 1e-9, f"float*float 应为 {expected}, got {r}"
    print(f"  float*float: {r} ✓")

    # 含 NaN 跳过
    s_n = Series([1.0, float("nan"), 3.0], name="x", dtype="float64")
    o_n = Series([10.0, 20.0, 30.0], name="y", dtype="float64")
    r = s_n.dot(o_n)
    # NaN 位置跳过，结果 = 1*10 + 3*30 = 100
    assert abs(r - 100.0) < 1e-9, f"含 NaN 应为 100.0, got {r}"
    print(f"  含 NaN 跳过: {r} ✓")

    # 含 None 跳过
    s_none = Series([1, None, 3], name="x", dtype="int64")
    o_none = Series([10, 20, 30], name="y", dtype="int64")
    r = s_none.dot(o_none)
    assert r == 100, f"含 None 应为 100, got {r}"
    print(f"  含 None 跳过: {r} ✓")

    # 长度不匹配抛 ValueError
    try:
        s.dot([1, 2, 3])
        assert False, "应抛 ValueError"
    except ValueError as e:
        print(f"  长度不匹配 ValueError: {e} ✓")

    # Bool * Int
    s_b = Series([True, False, True, True], name="x", dtype="bool")
    o_i = Series([1, 2, 3, 4], name="y", dtype="int64")
    r = s_b.dot(o_i)
    # 1*1 + 0*2 + 1*3 + 1*4 = 1 + 0 + 3 + 4 = 8
    assert r == 8, f"bool*int 应为 8, got {r}"
    print(f"  bool*int: {r} ✓")

    # 含字符串元素 → Python 回退路径会抛 TypeError
    s_str = Series([1, 2, 3], name="x", dtype="int64")
    try:
        s_str.dot(["a", "b", "c"])
        assert False, "应抛 TypeError"
    except TypeError:
        print(f"  含字符串 other: 抛 TypeError ✓")


def test_dot_performance():
    print("\n=== dot 性能 (500k 整数) ===")
    random.seed(42)
    n = 500_000
    s = Series([random.randint(-100, 100) for _ in range(n)], name="x", dtype="int64")
    other_list = [random.randint(-100, 100) for _ in range(n)]
    other = Series(other_list, name="y", dtype="int64")

    vals = s.values
    t_rust = _measure(lambda: s.dot(other), "Rust dot(Series)")
    t_py = _measure(lambda: _py_dot(vals, other_list), "Python dot")
    print(f"  加速比: {t_py / t_rust:.2f}x")

    # dot(list)
    t_rust_list = _measure(lambda: s.dot(other_list), "Rust dot(list)")
    print(f"  Rust dot(list) vs Rust dot(Series): {t_rust / t_rust_list:.2f}x")


def main():
    print("=" * 60)
    print("rspandas Rust 加速 dot 方法验证")
    print("=" * 60)

    test_dot_correctness()
    test_dot_performance()

    print("\n" + "=" * 60)
    print("全部测试通过 ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
