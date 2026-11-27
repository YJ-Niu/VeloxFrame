"""验证下沉到 Rust 的新一批方法：duplicated/mode/where/mask。

对每个方法执行：
1. 正确性测试：与 Python 实现（或 pandas 行为）对比
2. 性能测试：Rust 路径 vs Python 回退路径的加速比

运行：.venv/bin/python testing/verify/duplicated_mode_where_mask.py
"""

from __future__ import annotations

import random
import time
from collections import Counter
from typing import Any

import veloxframe as pd
from veloxframe import Series


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
    return Series([random.randint(-100, 100) for _ in range(n)], name="x", dtype="int64")


def _make_float_series(n: int, seed: int = 7) -> Series:
    random.seed(seed)
    return Series(
        [random.uniform(-100.0, 100.0) for _ in range(n)], name="x", dtype="float64"
    )


def _make_string_series(n: int, seed: int = 11) -> Series:
    random.seed(seed)
    pool = ["apple", "banana", "cherry", "date", "fig", "grape", "kiwi", "lemon"]
    return Series([random.choice(pool) for _ in range(n)], name="x", dtype="object")


# ============================================================
# Python 参考实现
# ============================================================


def _py_duplicated(values: list, keep) -> list:
    if keep == "first":
        seen: set = set()
        out = [v in seen or (seen.add(v), False)[1] for v in values]
    elif keep == "last":
        seen = set()
        rev_out = [v in seen or (seen.add(v), False)[1] for v in reversed(values)]
        out = list(reversed(rev_out))
    else:  # keep=False
        c = Counter(values)
        dup = {k for k, n in c.items() if n > 1}
        out = [v in dup for v in values]
    return out


def _py_mode(values: list) -> list:
    non_null = [v for v in values if v is not None]
    if not non_null:
        return []
    counter = Counter(non_null)
    max_count = max(counter.values())
    modes = [v for v, cnt in counter.items() if cnt == max_count]
    return sorted(modes)


def _py_where(values: list, cond: list, other: Any) -> list:
    return [v if c else other for v, c in zip(values, cond)]


def _py_mask(values: list, cond: list, other: Any) -> list:
    return [other if c else v for v, c in zip(values, cond)]


# ============================================================
# 正确性测试
# ============================================================


def test_duplicated_correctness():
    print("\n=== duplicated 正确性 ===")
    s = Series([1, 2, 1, 3, 2, 4], name="x", dtype="int64")

    # keep="first": 首次出现 False, 后续 True
    r = s.duplicated(keep="first")
    expected = [False, False, True, False, True, False]
    assert list(r.values) == expected, f"keep=first 应为 {expected}, got {list(r.values)}"
    print(f"  keep=first: {list(r.values)} ✓")

    # keep="last": 末次出现 False, 之前 True
    r = s.duplicated(keep="last")
    expected = [True, True, False, False, False, False]
    assert list(r.values) == expected, f"keep=last 应为 {expected}, got {list(r.values)}"
    print(f"  keep=last:  {list(r.values)} ✓")

    # keep=False: 所有重复值都为 True
    r = s.duplicated(keep=False)
    expected = [True, True, True, False, True, False]
    assert list(r.values) == expected, f"keep=False 应为 {expected}, got {list(r.values)}"
    print(f"  keep=False: {list(r.values)} ✓")

    # 含 None 的字符串列
    s_s = Series(["a", "b", "a", None, "b", None], name="x", dtype="object")
    r = s_s.duplicated(keep="first")
    expected = [False, False, True, False, True, True]
    assert list(r.values) == expected, f"含 None str 应为 {expected}, got {list(r.values)}"
    print(f"  含 None str keep=first: {list(r.values)} ✓")

    # Float 列（含 NaN，按位视为相同）
    s_f = Series([1.5, 2.0, 1.5, float("nan"), 2.0], name="x", dtype="float64")
    r = s_f.duplicated(keep="first")
    expected = [False, False, True, False, True]
    assert list(r.values) == expected, f"float keep=first 应为 {expected}, got {list(r.values)}"
    print(f"  float keep=first: {list(r.values)} ✓")

    # Bool 列
    s_b = Series([True, False, True, False, True], name="x", dtype="bool")
    r = s_b.duplicated(keep="first")
    expected = [False, False, True, True, True]
    assert list(r.values) == expected, f"bool keep=first 应为 {expected}, got {list(r.values)}"
    print(f"  bool keep=first: {list(r.values)} ✓")


def test_mode_correctness():
    print("\n=== mode 正确性 ===")
    # 单众数
    s = Series([1, 2, 2, 3, 3, 3], name="x", dtype="int64")
    r = s.mode()
    assert list(r.values) == [3], f"单众数应为 [3], got {list(r.values)}"
    print(f"  单众数: {list(r.values)} ✓")

    # 多众数（出现次数相同）
    s = Series([1, 1, 2, 2, 3], name="x", dtype="int64")
    r = s.mode()
    assert list(r.values) == [1, 2], f"多众数应为 [1, 2], got {list(r.values)}"
    print(f"  多众数: {list(r.values)} ✓")

    # 含 None 跳过
    s = Series([1, None, 1, 2, 2, None], name="x", dtype="int64")
    r = s.mode()
    assert list(r.values) == [1, 2], f"含 None 应为 [1, 2], got {list(r.values)}"
    print(f"  含 None 跳过: {list(r.values)} ✓")

    # Float 众数
    s_f = Series([1.5, 2.0, 1.5, 3.0, 2.0], name="x", dtype="float64")
    r = s_f.mode()
    assert list(r.values) == [1.5, 2.0], f"float 众数应为 [1.5, 2.0], got {list(r.values)}"
    print(f"  float 众数: {list(r.values)} ✓")

    # String 众数
    s_s = Series(["a", "b", "a", "c", "b"], name="x", dtype="object")
    r = s_s.mode()
    assert list(r.values) == ["a", "b"], f"str 众数应为 [a, b], got {list(r.values)}"
    print(f"  str 众数: {list(r.values)} ✓")

    # Bool 众数（false 在前，true 在后）
    s_b = Series([True, False, True, False, True], name="x", dtype="bool")
    r = s_b.mode()
    assert list(r.values) == [True], f"bool 众数应为 [True], got {list(r.values)}"
    print(f"  bool 众数: {list(r.values)} ✓")


def test_where_correctness():
    print("\n=== where/mask 正确性 ===")
    s = Series([1, 2, 3, 4, 5], name="x", dtype="int64")
    cond = [True, False, True, False, True]

    # where(cond, other=99): cond=True 保留原值, False 替换为 99
    r = s.where(cond, other=99)
    expected = [1, 99, 3, 99, 5]
    assert list(r.values) == expected, f"where 应为 {expected}, got {list(r.values)}"
    print(f"  where(标量): {list(r.values)} ✓")

    # mask(cond, other=99): cond=True 替换为 99, False 保留原值
    r = s.mask(cond, other=99)
    expected = [99, 2, 99, 4, 99]
    assert list(r.values) == expected, f"mask 应为 {expected}, got {list(r.values)}"
    print(f"  mask(标量): {list(r.values)} ✓")

    # where(cond, other=Series)
    other_s = Series([10, 20, 30, 40, 50], name="y", dtype="int64")
    r = s.where(cond, other=other_s)
    expected = [1, 20, 3, 40, 5]
    assert list(r.values) == expected, f"where(Series) 应为 {expected}, got {list(r.values)}"
    print(f"  where(Series): {list(r.values)} ✓")

    # mask(cond, other=Series)
    r = s.mask(cond, other=other_s)
    expected = [10, 2, 30, 4, 50]
    assert list(r.values) == expected, f"mask(Series) 应为 {expected}, got {list(r.values)}"
    print(f"  mask(Series): {list(r.values)} ✓")

    # Float 类型
    s_f = Series([1.5, 2.5, 3.5, 4.5], name="x", dtype="float64")
    r = s_f.where([True, False, True, False], other=0.0)
    expected = [1.5, 0.0, 3.5, 0.0]
    assert list(r.values) == expected, f"float where 应为 {expected}, got {list(r.values)}"
    print(f"  float where: {list(r.values)} ✓")

    # 含 None 的 Series
    s_n = Series([1, None, 3, None], name="x", dtype="int64")
    r = s_n.where([True, True, False, False], other=-1)
    expected = [1, None, -1, -1]
    result = list(r.values)
    for i, (a, e) in enumerate(zip(result, expected)):
        if e is None:
            assert a is None, f"位置 {i} 应为 None, got {a}"
        else:
            assert a == e, f"位置 {i} 应为 {e}, got {a}"
    print(f"  含 None where: {result} ✓")


# ============================================================
# 性能测试
# ============================================================


def test_duplicated_performance():
    print("\n=== duplicated 性能 (500k 整数, 100 唯一值) ===")
    s = _make_int_series(500_000)
    vals = s.values
    t_rust = _measure(lambda: s.duplicated(keep="first"), "Rust duplicated(keep=first)")
    t_py = _measure(lambda: _py_duplicated(vals, "first"), "Python duplicated(keep=first)")
    print(f"  加速比: {t_py / t_rust:.2f}x")


def test_mode_performance():
    print("\n=== mode 性能 (500k 整数, 200 唯一值) ===")
    s = _make_int_series(500_000)
    vals = s.values
    t_rust = _measure(lambda: s.mode(), "Rust mode")
    t_py = _measure(lambda: _py_mode(vals), "Python mode")
    print(f"  加速比: {t_py / t_rust:.2f}x")

    print("\n=== mode 性能 (100k 字符串, 8 唯一值) ===")
    s_s = _make_string_series(100_000)
    vals = s_s.values
    t_rust = _measure(lambda: s_s.mode(), "Rust mode(str)")
    t_py = _measure(lambda: _py_mode(vals), "Python mode(str)")
    print(f"  加速比: {t_py / t_rust:.2f}x")


def test_where_mask_performance():
    print("\n=== where/mask 性能 (500k 整数) ===")
    s = _make_int_series(500_000)
    random.seed(123)
    cond = [random.random() > 0.5 for _ in range(500_000)]
    vals = s.values

    t_rust_where = _measure(lambda: s.where(cond, other=99), "Rust where")
    t_py_where = _measure(lambda: _py_where(vals, cond, 99), "Python where")
    print(f"  where 加速比: {t_py_where / t_rust_where:.2f}x")

    t_rust_mask = _measure(lambda: s.mask(cond, other=99), "Rust mask")
    t_py_mask = _measure(lambda: _py_mask(vals, cond, 99), "Python mask")
    print(f"  mask 加速比: {t_py_mask / t_rust_mask:.2f}x")


def main():
    print("=" * 60)
    print("veloxframe 新一批 Rust 加速方法验证 (duplicated/mode/where/mask)")
    print("=" * 60)

    test_duplicated_correctness()
    test_mode_correctness()
    test_where_correctness()

    test_duplicated_performance()
    test_mode_performance()
    test_where_mask_performance()

    print("\n" + "=" * 60)
    print("全部测试通过 ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
