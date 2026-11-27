"""veloxframe.testing - 断言工具函数。

对齐主流库的 ``pandas.testing`` 命名空间：``assert_frame_equal`` /
``assert_series_equal`` / ``assert_index_equal``，用于测试中比较
DataFrame/Series/Index 是否相等。
"""

from __future__ import annotations

from .indexes import Index


def _as_list(obj) -> list:
    """Index 取底层数据，其他可迭代对象转 list。"""
    if isinstance(obj, Index):
        return list(obj._data)
    return list(obj)


def assert_index_equal(
    left,
    right,
    exact: bool = False,
    check_names: bool = True,
    check_exact: bool = True,
    check_order: bool = True,
    **kwargs,
) -> None:
    """断言两个索引相等 (主流库对齐)。

    :param left: 左索引
    :param right: 右索引
    :param exact: 是否要求 dtype 严格相等 (简化版：未启用)
    :param check_names: 是否比较 name
    :param check_exact: 数值是否要求完全相等 (False 时容忍 1e-5 误差)
    :param check_order: 是否要求顺序一致
    """
    l = _as_list(left)
    r = _as_list(right)
    if check_order:
        if len(l) != len(r):
            raise AssertionError(f"Index length mismatch: {len(l)} != {len(r)}")
        for i, (a, b) in enumerate(zip(l, r)):
            if a == b:
                continue
            if not check_exact and a is not None and b is not None:
                try:
                    if abs(float(a) - float(b)) < 1e-5:
                        continue
                except (TypeError, ValueError):
                    pass
            raise AssertionError(f"Index mismatch at position {i}: {a!r} != {b!r}")
    else:
        if sorted(map(str, l)) != sorted(map(str, r)):
            raise AssertionError(f"Index content mismatch: {l!r} != {r!r}")
    if check_names:
        ln = getattr(left, "name", None)
        rn = getattr(right, "name", None)
        if ln != rn:
            raise AssertionError(f"Index name mismatch: {ln!r} != {rn!r}")


def assert_series_equal(
    left,
    right,
    check_dtype: bool = True,
    check_index_type="equiv",
    check_names: bool = True,
    check_exact: bool = True,
    check_less_precise=False,
    **kwargs,
) -> None:
    """断言两个 Series 逐元素相等 (主流库对齐)。

    :param check_dtype: 是否比较 dtype
    :param check_names: 是否比较 name
    :param check_exact: 数值是否要求完全相等 (False 时容忍 1e-5 误差)
    """
    lv = list(left.values)
    rv = list(right.values)
    if len(lv) != len(rv):
        raise AssertionError(f"Series length mismatch: {len(lv)} != {len(rv)}")
    for i, (a, b) in enumerate(zip(lv, rv)):
        same = a == b
        if not same and a is not None and b is not None:
            try:
                same = a != a and b != b  # NaN == NaN
            except Exception:
                same = False
        if not same and not check_exact:
            try:
                same = abs(float(a) - float(b)) < 1e-5
            except (TypeError, ValueError):
                same = False
        if not same:
            raise AssertionError(
                f"Series value mismatch at position {i}: {a!r} != {b!r}"
            )
    if check_dtype:
        ld = str(left.dtype)
        rd = str(right.dtype)
        if ld != rd:
            raise AssertionError(f"Series dtype mismatch: {ld!r} != {rd!r}")
    if check_names and getattr(left, "name", None) != getattr(right, "name", None):
        raise AssertionError(
            f"Series name mismatch: {getattr(left, 'name', None)!r} != {getattr(right, 'name', None)!r}"
        )
    li = getattr(left, "_index", None)
    ri = getattr(right, "_index", None)
    if li is not None or ri is not None:
        if li is None or ri is None:
            raise AssertionError("one Series has an index, the other does not")
        assert_index_equal(li, ri)


def assert_frame_equal(
    left,
    right,
    check_dtype: bool = True,
    check_index_type="equiv",
    check_column_type="equiv",
    check_like: bool = False,
    check_names: bool = True,
    check_exact: bool = False,
    **kwargs,
) -> None:
    """断言两个 DataFrame 相等 (主流库对齐)。

    :param check_dtype: 是否比较列 dtype
    :param check_like: True 时允许列顺序不同 (按 left 列序重排 right)
    :param check_names: 是否比较 name
    :param check_exact: 数值是否要求完全相等 (False 时容忍 1e-5 误差)
    """
    lc = list(left.columns)
    rc = list(right.columns)
    if check_like:
        if set(lc) != set(rc):
            raise AssertionError(f"column set mismatch: {lc!r} != {rc!r}")
        right = right[lc]
    elif lc != rc:
        raise AssertionError(f"column mismatch: {lc!r} != {rc!r}")
    li = left._index if left._index is not None else list(range(len(left)))
    ri = right._index if right._index is not None else list(range(len(right)))
    assert_index_equal(li, ri)
    for c in lc:
        assert_series_equal(
            left[c],
            right[c],
            check_dtype=check_dtype,
            check_names=check_names,
            check_exact=check_exact,
        )


__all__ = [
    "assert_frame_equal",
    "assert_series_equal",
    "assert_index_equal",
]
