"""veloxframe: DataFrame-like library built on Rust.

A drop-in DataFrame-like API where the heavy lifting is done in Rust.
"""

# ============================================================================
# 类型常量
# ============================================================================
from ._scalars import (
    Categorical,
    DateOffset,
    Interval,
    NA,
    NaT,
    Period,
    Timestamp,
    Timedelta,
)
from . import offsets
from ._datetime import (
    bdate_range,
    date_range,
    DatetimeSeries,
    infer_freq,
    period_range,
    timedelta_range,
    to_datetime,
    to_timedelta,
)
from .dataframe import DataFrame
from .indexes import (
    CategoricalIndex,
    DatetimeIndex,
    IntervalIndex,
    PeriodIndex,
    TimedeltaIndex,
    crosstab,
    cut,
    get_dummies,
    Index,
    MultiIndex,
    qcut,
    RangeIndex,
)
from . import api
from . import errors, testing
from .io import (
    ExcelWriter,
    read_csv_chunked,
    read_clipboard,
    read_excel,
    read_feather,
    read_gbq,
    read_hdf,
    read_html,
    read_json,
    read_orc,
    read_parquet,
    read_pickle,
    read_spss,
    read_sql,
    read_sql_query,
    read_sql_table,
    read_stata,
    read_xml,
    StreamDataFrame,
    to_clipboard,
    to_excel,
    to_feather,
    to_gbq,
    to_hdf,
    to_html,
    to_json,
    to_orc,
    to_parquet,
    to_pickle,
    to_sql,
    to_sql_batch,
    to_stata,
    to_xml,
)
from .lazyframe import LazyFrame, lazy, col, lit
from .veloxframe import _DataFrame, _Series  # 重新导出 Rust 类型，供内部使用
from .veloxframe import factorize as _factorize  # Rust 端 factorize
from .series import Series
from typing import Any, Dict

# ---------------------------------------------------------------------------
# 全局选项配置
# ---------------------------------------------------------------------------

_options: Dict[str, Any] = {
    "display.max_rows": 60,
    "display.max_columns": 8,
    "display.width": 80,
    "display.precision": 6,
    "display.max_colwidth": 50,
    "display.max_info_rows": 1690785,
    "display.max_info_columns": 100,
    "display.expand_frame_repr": True,
    "display.large_repr": "truncate",
    "display.memory_usage": True,
    "display.float_format": None,
    "display.colheader_justify": "right",
    "display.date_dayfirst": False,
    "display.date_yearfirst": False,
    "display.unicode.east_asian_width": False,
    "display.unicode.ambiguous_as_wide": False,
    "display.html.border": 1,
    "display.html.table_schema": False,
    "display.html.use_mathjax": True,
    "display.latex.escape": True,
    "display.latex.longtable": False,
    "display.latex.repr": False,
    "mode.chained_assignment": "warn",
    "mode.use_inf_as_na": False,
    "compute.use_bottleneck": True,
    "compute.use_numexpr": True,
}

# 默认选项的副本（用于 reset_option）
_defaults: Dict[str, Any] = dict(_options)


def set_option(pat: str, value: Any) -> None:
    """设置全局选项。

    :param pat: 选项名 (如 'display.max_rows')
    :param value: 选项值
    """
    if pat in _options:
        _options[pat] = value
    else:
        raise ValueError(f"Unknown option: {pat!r}")


def get_option(pat: str) -> Any:
    """获取全局选项。

    :param pat: 选项名 (如 'display.max_rows')
    """
    if pat in _options:
        return _options[pat]
    raise ValueError(f"Unknown option: {pat!r}")


def reset_option(pat: str) -> None:
    """重置选项为默认值。

    :param pat: 选项名 (如 'display.max_rows')，或 'all' 重置全部
    """
    if pat in _defaults:
        _options[pat] = _defaults[pat]
    elif pat == "all":
        # 使用 dict.update 替代显式 for 循环
        _options.update(_defaults)
    else:
        raise ValueError(f"Unknown option: {pat!r}")


def factorize(values):
    """对值进行编码，返回 (codes, categories)。

    Examples:
        >>> import veloxframe as rpd
        >>> codes, cats = rpd.factorize(['a', 'b', 'a', 'c', 'b'])
        >>> list(codes)
        [0, 1, 0, 2, 1]
        >>> list(cats)
        ['a', 'b', 'c']
    """
    return _factorize(values)


def to_numeric(arg, errors: str = "raise", downcast=None):
    """将参数转换为数值类型。

    :param arg: list / Series / 标量
    :param errors: 'raise' / 'coerce' / 'ignore'
    :param downcast: None / 'integer' / 'signed' / 'unsigned' / 'float'
    :return: 标量输入返回标量；list/tuple 输入返回 ndarray；Series 输入返回 Series

    Examples:
        >>> to_numeric(['1', '2', '3'])
        array([1, 2, 3])
        >>> to_numeric(['1', 'x', '3'], errors='coerce')
        array([1.0, nan, 3.0])
    """
    import math
    from .series import Series as _Series

    if isinstance(arg, _Series):
        values = list(arg.values)
    elif isinstance(arg, (list, tuple)):
        values = list(arg)
    else:
        # 标量
        try:
            v = float(arg)
            if v == int(v) and not isinstance(arg, bool):
                return int(v)
            return v
        except (ValueError, TypeError):
            if errors == "coerce":
                return math.nan
            if errors == "ignore":
                return arg
            raise ValueError(f"Unable to parse string {arg!r}")

    def _convert_one(v):
        """将单个值转换为数值，根据 errors 决定异常处理方式。"""
        if v is None:
            return math.nan if errors == "coerce" else None
        try:
            # 注意：bool 是 int 的子类，需保持与原实现一致的判断顺序
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (int, float)):
                return v
            if isinstance(v, str):
                s = v.strip()
                if s == "":
                    return math.nan if errors == "coerce" else v
                val = float(s)
                if val == int(val) and "." not in s and "e" not in s.lower():
                    return int(val)
                return val
            try:
                return float(v)
            except (ValueError, TypeError):
                if errors == "coerce":
                    return math.nan
                if errors == "ignore":
                    return v
                raise ValueError(f"Unable to parse {v!r}")
        except (ValueError, TypeError):
            if errors == "coerce":
                return math.nan
            if errors == "ignore":
                return v
            raise

    result = [_convert_one(v) for v in values]

    # downcast 逻辑（对齐 主流库）
    # 'integer'/'signed' -> int8/int16/int32/int64 中能容纳所有值的最小 dtype
    # 'unsigned' -> uint8/uint16/uint32/uint64
    # 'float' -> float32（如果所有值都在 float32 范围内）
    downcast_dtype = None
    if downcast:
        if downcast in ("integer", "signed"):
            # 所有值必须为整数（或 nan）
            int_vals = [
                v
                for v in result
                if v is not None and not (isinstance(v, float) and math.isnan(v))
            ]
            if all(isinstance(v, int) for v in int_vals):
                # 计算范围，选择最小 dtype
                if int_vals:
                    vmin, vmax = min(int_vals), max(int_vals)
                    if vmin >= -128 and vmax <= 127:
                        downcast_dtype = "int8"
                    elif vmin >= -32768 and vmax <= 32767:
                        downcast_dtype = "int16"
                    elif vmin >= -2147483648 and vmax <= 2147483647:
                        downcast_dtype = "int32"
                    else:
                        downcast_dtype = "int64"
        elif downcast == "unsigned":
            int_vals = [
                v
                for v in result
                if v is not None and not (isinstance(v, float) and math.isnan(v))
            ]
            if all(isinstance(v, int) and v >= 0 for v in int_vals):
                if int_vals:
                    vmax = max(int_vals)
                    if vmax <= 255:
                        downcast_dtype = "uint8"
                    elif vmax <= 65535:
                        downcast_dtype = "uint16"
                    elif vmax <= 4294967295:
                        downcast_dtype = "uint32"
                    else:
                        downcast_dtype = "uint64"
        elif downcast == "float":
            # 如果所有值都能用 float32 表示，则 downcast 为 float32
            downcast_dtype = "float32"

    # 对 list/tuple 输入返回 ndarray（对齐 主流库 行为）
    if isinstance(arg, (list, tuple)):
        import rsarray as _rnp

        arr = _rnp.asarray(result)
        # 应用 downcast dtype
        if downcast_dtype:
            arr._dtype = downcast_dtype
        return arr
    # 对 Series 输入返回 Series
    s = _Series(result, name=None)
    if downcast_dtype:
        s._dtype_str = downcast_dtype
    return s


def merge(
    left,
    right,
    how: str = "inner",
    on=None,
    left_on=None,
    right_on=None,
    left_index: bool = False,
    right_index: bool = False,
    sort: bool = False,
    suffixes=("_x", "_y"),
) -> "DataFrame":
    """合并两个 DataFrame。

    :param left: 左侧 DataFrame
    :param right: 右侧 DataFrame
    :param how: 合并方式 ('inner'/'outer'/'left'/'right')
    :param on: 合并键列
    :param left_on: 左侧合并键
    :param right_on: 右侧合并键
    :param left_index: 是否使用左侧索引
    :param right_index: 是否使用右侧索引
    :param sort: 是否排序
    :param suffixes: 重复列的后缀
    """
    if not isinstance(left, DataFrame) or not isinstance(right, DataFrame):
        raise TypeError("merge requires DataFrame inputs")
    return left.merge(
        right,
        how=how,
        on=on,
        left_on=left_on,
        right_on=right_on,
        left_index=left_index,
        right_index=right_index,
        sort=sort,
        suffixes=suffixes,
    )


def concat(
    objs, axis: int = 0, join: str = "outer", ignore_index: bool = False
) -> "Series":
    """拼接多个 Series 或 DataFrame。

    :param objs: 要拼接的对象列表
    :param axis: 拼接轴 (0=纵向, 1=横向)
    :param join: 连接方式 ('outer'/'inner')
    :param ignore_index: 是否忽略索引
    """
    from .series import Series as _Series
    from itertools import chain

    if not objs:
        return _Series([])

    if all(isinstance(o, _Series) for o in objs):
        all_values = list(chain.from_iterable(list(s.values) for s in objs))
        if ignore_index:
            return _Series(all_values)
        all_index = list(
            chain.from_iterable(
                (s._index if s._index else list(range(len(s)))) for s in objs
            )
        )
        return _Series(all_values, index=all_index)

    if all(isinstance(o, DataFrame) for o in objs):
        # 收集列名：join="inner" 仅保留所有表共有列（按首表顺序），
        # 否则取并集（保留首次出现顺序），与主流库默认 join='outer' 一致
        if join == "inner":
            all_columns = [
                c for c in objs[0]._columns if all(c in df._columns for df in objs)
            ]
        else:
            all_columns = list(dict.fromkeys(c for df in objs for c in df._columns))
        all_data = {
            col: list(
                chain.from_iterable(
                    (
                        list(df._inner.get_column(col).values)
                        if col in df._columns
                        else [None] * df._nrows
                    )
                    for df in objs
                )
            )
            for col in all_columns
        }
        return DataFrame(all_data)

    raise TypeError("concat requires all objects of the same type")


def isnull(obj):
    """检测缺失值 (None 或 NaN)。"""
    if isinstance(obj, (Series, _Series)):
        return obj.isnull()
    elif isinstance(obj, DataFrame):
        return obj.isnull()
    elif isinstance(obj, list):
        return [v is None or (isinstance(v, float) and v != v) for v in obj]
    elif hasattr(obj, "tolist") and hasattr(obj, "dtype"):
        # rsarray.ndarray: 逐元素检测 NaN
        import rsarray as _rnp

        vals = obj.tolist() if hasattr(obj, "tolist") else list(obj)
        mask = [v is None or (isinstance(v, float) and v != v) for v in vals]
        return _rnp.array(mask)
    else:
        return obj is None or (isinstance(obj, float) and obj != obj)


def notnull(obj):
    """检测非缺失值。"""
    if isinstance(obj, (Series, _Series)):
        return obj.notnull()
    elif isinstance(obj, DataFrame):
        return obj.notnull()
    elif isinstance(obj, list):
        return [v is not None and not (isinstance(v, float) and v != v) for v in obj]
    elif hasattr(obj, "tolist") and hasattr(obj, "dtype"):
        # rsarray.ndarray: 逐元素检测非缺失
        import rsarray as _rnp

        vals = obj.tolist() if hasattr(obj, "tolist") else list(obj)
        mask = [v is not None and not (isinstance(v, float) and v != v) for v in vals]
        return _rnp.array(mask)
    else:
        return obj is not None and not (isinstance(obj, float) and obj != obj)


# isna / notna 别名
isna = isnull
notna = notnull


def unique(values):
    """返回唯一值。"""
    if isinstance(values, (Series, _Series)):
        return values.unique()
    elif isinstance(values, list):
        # 利用 dict.fromkeys 保序去重（Python 3.7+ dict 保持插入顺序）
        return list(dict.fromkeys(values))
    raise TypeError("unique requires Series or list")


def value_counts(
    values, normalize: bool = False, sort: bool = True, ascending: bool = False
) -> _Series:
    """统计值出现次数。"""
    if isinstance(values, (Series, _Series)):
        return values.value_counts()
    elif isinstance(values, list):
        s = _Series(values)
        return s.value_counts()
    raise TypeError("value_counts requires Series or list")


__version__ = "1.0.1"
__all__ = [
    "Series",
    "DataFrame",
    "LazyFrame",
    "lazy",
    "col",
    "lit",
    "to_datetime",
    "date_range",
    "to_timedelta",
    "timedelta_range",
    "period_range",
    "bdate_range",
    "infer_freq",
    "DatetimeSeries",
    "factorize",
    "read_json",
    "to_json",
    "read_html",
    "to_html",
    "read_clipboard",
    "to_clipboard",
    "read_xml",
    "to_xml",
    "read_orc",
    "to_orc",
    "read_stata",
    "to_stata",
    "read_hdf",
    "to_hdf",
    "read_spss",
    "read_gbq",
    "to_gbq",
    "read_excel",
    "to_excel",
    "ExcelWriter",
    "read_parquet",
    "to_parquet",
    "read_feather",
    "to_feather",
    "read_pickle",
    "to_pickle",
    "read_sql",
    "read_sql_query",
    "read_sql_table",
    "read_csv_chunked",
    "StreamDataFrame",
    "to_sql",
    "to_sql_batch",
    "Index",
    "RangeIndex",
    "MultiIndex",
    "DatetimeIndex",
    "CategoricalIndex",
    "PeriodIndex",
    "TimedeltaIndex",
    "get_dummies",
    "cut",
    "qcut",
    "crosstab",
    "offsets",
    "set_option",
    "get_option",
    "reset_option",
    "to_numeric",
    "merge",
    "merge_asof",
    "merge_ordered",
    "merge_wide_to_long",
    "interval_range",
    "NamedAgg",
    "named_agg",
    "IntervalIndex",
    "errors",
    "testing",
    "concat",
    "pivot",
    "pivot_table",
    "melt",
    "option_context",
    "options",
    "wide_to_long",
    "lreshape",
    "isnull",
    "notnull",
    "isna",
    "notna",
    "unique",
    "value_counts",
    "Timestamp",
    "Timedelta",
    "Period",
    "Interval",
    "Categorical",
    "DateOffset",
    "NaT",
    "NA",
    "array",
    "api",
    "test",
    "_Series",
    "_DataFrame",
    "__version__",
]


# ============================================================================
# 顶层缺失函数补全
# ============================================================================


def melt(
    frame,
    id_vars=None,
    value_vars=None,
    var_name: str = "variable",
    value_name: str = "value",
    col_level=0,
    ignore_index: bool = True,
):
    """宽表转长表 (顶层入口，等价于 ``DataFrame.melt``)。

    :param frame: 输入 DataFrame
    :param id_vars: 标识符列 (str | list | None)
    :param value_vars: 要展开为值的列 (str | list | None)
    :param var_name: 存放原列名的列名
    :param value_name: 存放原值的列名
    :param col_level: 多级列时取用的层级 (仅用于签名兼容)
    :param ignore_index: 是否重置索引
    :return: DataFrame
    """
    if not isinstance(frame, DataFrame):
        raise TypeError("melt requires a DataFrame")
    return frame.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name=var_name,
        value_name=value_name,
        ignore_index=ignore_index,
    )


def pivot(
    table,
    index=None,
    columns=None,
    values=None,
):
    """长表转宽表 (顶层入口，等价于 ``DataFrame.pivot``)。

    :param table: 输入 DataFrame
    :param index: 用作行索引的列 (str | None)
    :param columns: 用作列的列 (str)
    :param values: 填充值的列 (str | list | None)
    :return: DataFrame
    """
    if not isinstance(table, DataFrame):
        raise TypeError("pivot requires a DataFrame")
    return table.pivot(index=index, columns=columns, values=values)


class option_context:
    """临时修改全局选项的上下文管理器。

    进入时应用传入的键值对，退出时恢复原值。等价于
    ``with rpd.option_context('display.max_rows', 10) as ctx: ...``。

    Examples:
        >>> with rpd.option_context("display.max_rows", 5, "display.width", 40):
        ...     print(rpd.get_option("display.max_rows"))
        5
    """

    def __init__(self, *args):
        # 支持 option_context("a.b", 1, "c.d", 2) 成对传入
        if len(args) % 2 != 0:
            raise ValueError(
                "option_context requires key-value pairs "
                "(an even number of arguments)"
            )
        self._pairs = [(args[i], args[i + 1]) for i in range(0, len(args), 2)]
        self._saved: Dict[str, Any] = {}

    def __enter__(self):
        for pat, value in self._pairs:
            try:
                self._saved[pat] = get_option(pat)
            except Exception:
                self._saved[pat] = None
            set_option(pat, value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for pat, value in self._pairs:
            # 若期间被删除则恢复为 None（不存在即视为默认）
            try:
                set_option(pat, self._saved.get(pat))
            except Exception:
                pass
        return False


# ============================================================================
# rsarray 函数包装 - 让 rnp.exp(Series) 返回 Series 而非 ndarray
# ============================================================================


def read_csv(
    filepath_or_buffer,
    sep=",",
    delimiter=None,
    header="infer",
    names=None,
    index_col=None,
    usecols=None,
    dtype=None,
    engine=None,
    converters=None,
    true_values=None,
    false_values=None,
    skipinitialspace: bool = False,
    skiprows=None,
    skipfooter: int = 0,
    nrows=None,
    na_values=None,
    keep_default_na: bool = True,
    na_filter: bool = True,
    verbose: bool = False,
    skip_blank_lines: bool = True,
    parse_dates=None,
    infer_datetime_format: bool = False,
    keep_date_col: bool = False,
    date_parser=None,
    date_format=None,
    dayfirst: bool = False,
    cache_dates: bool = True,
    iterator: bool = False,
    chunksize=None,
    compression: str = "infer",
    encoding: str = None,
    encoding_errors: str = "strict",
    lineterminator=None,
    quotechar: str = '"',
    quoting=0,
    doublequote: bool = True,
    escapechar=None,
    comment=None,
    decimal: str = ".",
    thousands=None,
    storage_options=None,
    dtype_backend=None,
):
    """读取 CSV 文件为 DataFrame。"""
    from .io import read_csv as _read_csv

    return _read_csv(
        filepath_or_buffer,
        sep=sep,
        delimiter=delimiter,
        header=header,
        names=names,
        index_col=index_col,
        usecols=usecols,
        dtype=dtype,
        engine=engine,
        converters=converters,
        true_values=true_values,
        false_values=false_values,
        skipinitialspace=skipinitialspace,
        skiprows=skiprows,
        skipfooter=skipfooter,
        nrows=nrows,
        na_values=na_values,
        keep_default_na=keep_default_na,
        na_filter=na_filter,
        skip_blank_lines=skip_blank_lines,
        parse_dates=parse_dates,
        date_format=date_format,
        dayfirst=dayfirst,
        cache_dates=cache_dates,
        iterator=iterator,
        chunksize=chunksize,
        compression=compression,
        encoding=encoding,
        encoding_errors=encoding_errors,
        lineterminator=lineterminator,
        quotechar=quotechar,
        quoting=quoting,
        doublequote=doublequote,
        escapechar=escapechar,
        comment=comment,
        decimal=decimal,
        thousands=thousands,
        storage_options=storage_options,
        dtype_backend=dtype_backend,
    )


def merge_asof(
    left,
    right,
    on=None,
    left_on=None,
    right_on=None,
    left_index: bool = False,
    right_index: bool = False,
    by=None,
    left_by=None,
    right_by=None,
    suffixes=("_x", "_y"),
    tolerance=None,
    allow_exact_matches: bool = True,
    direction: str = "backward",
):
    """近似合并（asof join）。

    根据 on 列找最近邻的匹配行，常用于金融时间序列对齐。
    """
    from .dataframe import DataFrame

    if not isinstance(left, DataFrame) or not isinstance(right, DataFrame):
        raise TypeError("merge_asof requires DataFrame inputs")

    # 简化实现：按 on 列排序后逐行查找最近邻
    left_on = left_on or on
    right_on = right_on or on
    if left_on is None or right_on is None:
        raise ValueError("merge_asof requires 'on' or 'left_on'/'right_on'")

    left_sorted = left.sort_values(by=left_on).reset_index(drop=True)
    right_sorted = right.sort_values(by=right_on).reset_index(drop=True)

    # 简化：只支持 backward 方向
    right_vals = list(right_sorted[right_on].values)
    left_vals = list(left_sorted[left_on].values)

    def _find_match_idx(left_val):
        """在 right_vals 中查找匹配的索引，找不到返回 -1。"""
        if direction == "backward":
            # right_vals 已升序排序，反向找最后一个 <= left_val 的非 None 索引
            return next(
                (
                    i
                    for i in range(len(right_vals) - 1, -1, -1)
                    if right_vals[i] is not None
                    and left_val is not None
                    and right_vals[i] <= left_val
                ),
                -1,
            )
        if direction == "forward":
            # 找第一个 >= left_val 的非 None 索引
            return next(
                (
                    i
                    for i, rv in enumerate(right_vals)
                    if rv is not None and left_val is not None and rv >= left_val
                ),
                -1,
            )
        if direction == "nearest":
            # 找差值绝对值最小的索引
            candidates = [
                (i, abs(rv - left_val))
                for i, rv in enumerate(right_vals)
                if rv is not None and left_val is not None
            ]
            if not candidates:
                return -1
            return min(candidates, key=lambda x: x[1])[0]
        return -1

    def _build_row(left_val, match_idx):
        """根据 left_val 和匹配索引构建结果行。"""
        left_row_idx = left_vals.index(left_val)
        row = {c: left_sorted[c].values[left_row_idx] for c in left_sorted._columns}
        if match_idx >= 0:
            row.update(
                {
                    (c if c not in row else f"{c}{suffixes[1]}"): right_sorted[
                        c
                    ].values[match_idx]
                    for c in right_sorted._columns
                    if c != right_on
                }
            )
        return row

    result_rows = [
        _build_row(left_val, match_idx)
        for left_val in left_vals
        for match_idx in [_find_match_idx(left_val)]
        if match_idx >= 0 or allow_exact_matches
    ]

    return DataFrame(result_rows)


def pivot_table(
    data,
    values=None,
    index=None,
    columns=None,
    aggfunc: str = "mean",
    fill_value=None,
    margins: bool = False,
    dropna: bool = True,
    margins_name: str = "All",
) -> "DataFrame":
    """创建透视表（顶层函数）。

    :param data: 输入 DataFrame
    :param values: 聚合的列 (str | list[str] | None -> 所有数值列)
    :param index: 行分组列 (str | list[str])
    :param columns: 列分组列 (str | list[str])
    :param aggfunc: 聚合函数 (str, 默认 'mean')
    :param fill_value: 填充缺失值的值
    :param margins: 是否添加边界行/列
    :param dropna: 是否删除全 NaN 行/列
    :param margins_name: 边界行/列的名称
    :return: DataFrame
    """
    return data.pivot_table(
        values=values,
        index=index,
        columns=columns,
        aggfunc=aggfunc,
        fill_value=fill_value,
        margins=margins,
        dropna=dropna,
        margins_name=margins_name,
    )


def wide_to_long(
    df,
    stubnames,
    i,
    j,
    sep: str = "",
    suffix: str = r"\d+",
):
    """宽表转长表。

    :param df: 输入 DataFrame
    :param stubnames: stubname 列名列表
    :param i: id 列名列表
    :param j: 子变量列名
    :param sep: stubname 与后缀的分隔符
    :param suffix: 后缀正则
    """
    from .dataframe import DataFrame

    if isinstance(stubnames, str):
        stubnames = [stubnames]
    if isinstance(i, str):
        i = [i]

    def _suffix(col, stub, sep):
        """提取列名中 stub+sep 之后的部分作为后缀值。"""
        offset = len(stub) + len(sep)
        return col[offset:]

    # 三层循环展开为列表推导式：行索引 × stub × 匹配列
    result_rows = [
        {
            **{col: df[col].values[idx_val] for col in i},
            j: _suffix(col, stub, sep),
            stub: df[col].values[idx_val],
        }
        for idx_val in range(len(df))
        for stub in stubnames
        for col in df._columns
        if col != stub and col.startswith(stub + sep)
    ]

    return DataFrame(result_rows)


def lreshape(
    df,
    groups,
    dropna: bool = True,
):
    """宽转长（旧版）。

    :param df: 输入 DataFrame
    :param groups: {新列名: [原列名列表]}
    :param dropna: 是否删除缺失值
    """
    from .dataframe import DataFrame

    # 找出所有 id 列（不在任何 group 中的列）—— 集合推导式收集 group 列
    group_cols = {c for cols in groups.values() for c in cols}
    id_cols = [c for c in df._columns if c not in group_cols]

    # 三层循环展开为列表推导式：行索引 × group × 源列
    result_rows = [
        {
            **{c: df[c].values[i] for c in id_cols},
            new_col: df[src].values[i],
        }
        for i in range(len(df))
        for new_col, src_cols in groups.items()
        for src in src_cols
        if not dropna or df[src].values[i] is not None
    ]

    return DataFrame(result_rows)


# ============================================================================
# 顶层缺失函数补全（续）：merge_ordered / merge_wide_to_long / interval_range
# ============================================================================

from collections import namedtuple as _namedtuple

NamedAgg = _namedtuple("NamedAgg", ["column", "aggfunc"])


def merge_ordered(
    left,
    right,
    on=None,
    left_on=None,
    right_on=None,
    fill_method=None,
    **kwargs,
):
    """对已排序数据进行有序外连接 (主流库对齐)。

    两表按键对齐，缺失的一侧用 None 填充；fill_method='ffill' 时
    缺失值按前值填充。

    :param left: 左侧 DataFrame
    :param right: 右侧 DataFrame
    :param on: 两侧共用的键列名
    :param left_on: 左侧键列名
    :param right_on: 右侧键列名
    :param fill_method: None / 'ffill' / 'bfill'
    """
    if on is not None:
        left_on = right_on = on
    if left_on is None or right_on is None:
        raise ValueError("must provide 'on', or both 'left_on' and 'right_on'")
    key_col = on if on is not None else left_on
    lkeys = list(left[left_on].values)
    rkeys = list(right[right_on].values)

    # 两侧均有序时按键归并 (保序)
    all_keys = None
    try:
        l_sorted = all(a <= b for a, b in zip(lkeys, lkeys[1:]))
        r_sorted = all(a <= b for a, b in zip(rkeys, rkeys[1:]))
    except TypeError:
        l_sorted = r_sorted = False
    if l_sorted and r_sorted:
        merged_keys = []
        i = j = 0
        while i < len(lkeys) and j < len(rkeys):
            if lkeys[i] < rkeys[j]:
                merged_keys.append(lkeys[i])
                i += 1
            elif lkeys[i] > rkeys[j]:
                merged_keys.append(rkeys[j])
                j += 1
            else:
                merged_keys.append(lkeys[i])
                i += 1
                j += 1
        merged_keys.extend(lkeys[i:])
        merged_keys.extend(rkeys[j:])
        # 去重保序：唯一键序列，重复键的行由 l_map/r_map 笛卡尔积展开
        try:
            seen = set()
            all_keys = [k for k in merged_keys if not (k in seen or seen.add(k))]
        except TypeError:
            all_keys = []
            for k in merged_keys:
                if k not in all_keys:
                    all_keys.append(k)
    else:
        all_keys = list(dict.fromkeys(list(lkeys) + list(rkeys)))

    l_map = {}
    for i, k in enumerate(lkeys):
        l_map.setdefault(k, []).append(i)
    r_map = {}
    for i, k in enumerate(rkeys):
        r_map.setdefault(k, []).append(i)

    l_cols = [c for c in left.columns if c != left_on]
    r_cols = [c for c in right.columns if c != right_on]
    l_data = {c: list(left[c].values) for c in l_cols}
    r_data = {c: list(right[c].values) for c in r_cols}
    # 冲突列加 _y 后缀
    r_renamed = {}
    for c in r_cols:
        if c in l_cols or c == key_col:
            r_renamed[c] = c + "_y"
        else:
            r_renamed[c] = c

    out = {key_col: []}
    for c in l_cols:
        out[c] = []
    for name in r_renamed.values():
        out[name] = []
    for k in all_keys:
        lis = l_map.get(k, [None])
        ris = r_map.get(k, [None])
        for li in lis:
            for ri in ris:
                out[key_col].append(k)
                for c in l_cols:
                    out[c].append(l_data[c][li] if li is not None else None)
                for c in r_cols:
                    out[r_renamed[c]].append(r_data[c][ri] if ri is not None else None)

    if fill_method:
        for c in out:
            if c == key_col:
                continue
            vals = out[c]
            if fill_method == "ffill":
                last = None
                for i, v in enumerate(vals):
                    if v is None:
                        vals[i] = last
                    else:
                        last = v
            elif fill_method == "bfill":
                nxt = None
                for i in range(len(vals) - 1, -1, -1):
                    if vals[i] is None:
                        vals[i] = nxt
                    else:
                        nxt = vals[i]
            else:
                raise ValueError(f"invalid fill_method: {fill_method!r}")
    return DataFrame(out)


def merge_wide_to_long(
    df, stubnames, iaxis=0, mcols=None, sep="", junct="_", suffix=None
):
    """宽表转长表 (主流库对齐，简化版)。

    :param df: 宽表 DataFrame
    :param stubnames: 存根列前缀列表，如 ['A', 'B'] (对应 A_1, A_2, ...)
    :param iaxis: 后缀列名 (存根后缀对应的列)
    :param mcols: 需要逐行重复的其他标识列
    :param sep: 存根与后缀间的分隔符
    :param junct: 输出列名连接符 (保留参数)
    :param suffix: 后缀集合；None 时自动检测
    """
    cols = list(df.columns)
    stubs = list(stubnames)
    mcols = list(mcols) if mcols is not None else []
    data = {c: list(df[c].values) for c in cols}
    n = len(data[cols[0]]) if cols else 0
    if suffix is None:
        sfx = set()
        for stub in stubs:
            prefix = f"{stub}{sep}"
            for c in cols:
                if c.startswith(prefix):
                    sfx.add(c[len(prefix) :])
        if not sfx:
            raise ValueError(f"no columns matching stubs {stubs!r}")
        suffix = sorted(sfx)

    # iaxis 列取原行值并按后缀重复 (pandas 语义)；非列时回退为行号
    iaxis_data = data.get(str(iaxis))
    if iaxis_data is None:
        iaxis_data = list(range(n))

    out = {m: [] for m in mcols}
    out[iaxis] = []
    for stub in stubs:
        out[stub] = []
    for i in range(n):
        for s in suffix:
            for m in mcols:
                out[m].append(data[m][i])
            out[iaxis].append(iaxis_data[i])
            for stub in stubs:
                col = f"{stub}{sep}{s}"
                if col not in data:
                    raise ValueError(f"missing column {col!r} for stub {stub!r}")
                out[stub].append(data[col][i])
    return DataFrame(out)


def named_agg(*args, **kwargs) -> dict:
    """pandas named_agg: 将关键字参数转换为 NamedAgg 对象字典。

    用法::

        df.agg(veloxframe.named_agg(total=("amount", "sum"), peak=("amount", "max")))

    :param args: 兼容占位 (pandas 同样忽略位置参数)
    :param kwargs: 名称 → (column, aggfunc) 元组或 NamedAgg
    """
    out = {}
    for name, spec in kwargs.items():
        if isinstance(spec, tuple) and len(spec) == 2:
            out[name] = NamedAgg(spec[0], spec[1])
        elif isinstance(spec, NamedAgg):
            out[name] = spec
        else:
            raise TypeError(
                f"named_agg({name}=...) expects (column, aggfunc) or NamedAgg"
            )
    return out


class _OptionsNamespace:
    """pd.options 风格属性命名空间: 读写全局选项。

    ``options.display.max_rows = 5`` 等价于 ``set_option("display.max_rows", 5)``;
    读叶子返回选项值, 读中间节点返回子命名空间。
    """

    def __init__(self, root: str = ""):
        object.__setattr__(self, "_root", root)

    def _key(self, name: str) -> str:
        root = object.__getattribute__(self, "_root")
        return f"{root}.{name}" if root else name

    def __getattr__(self, name):
        key = self._key(name)
        try:
            return get_option(key)
        except ValueError:
            return _OptionsNamespace(key)

    def __setattr__(self, name, value):
        set_option(self._key(name), value)

    def __repr__(self):
        return f"<options {object.__getattribute__(self, '_root') or '(root)'}>"


options = _OptionsNamespace()


def show_versions(as_json: bool = False) -> None:
    """打印 veloxframe 及依赖版本信息 (用于 issue 报告)。

    :param as_json: 以 JSON 格式输出 (默认 False，按 键: 值 行输出)
    """
    import json
    import platform
    import sys

    info = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "machine": platform.machine(),
        "OS": platform.system(),
        "OS-release": platform.release(),
        "veloxframe": __version__,
        "rsarray": None,
    }
    try:
        import rsarray

        info["rsarray"] = getattr(rsarray, "__version__", "unknown")
    except ImportError:
        pass
    if as_json:
        print(json.dumps(info, indent=2))
    else:
        for k, v in info.items():
            print(f"{k}: {v}")


def interval_range(
    start=None, end=None, periods=None, freq=None, closed: str = "right", name=None
):
    """生成 IntervalIndex (主流库对齐，简化版：数值区间 + 数值步长)。

    start/end/periods/freq 中至少给出三个。

    :param start: 起点
    :param end: 终点
    :param periods: 区间个数
    :param freq: 步长 (数值)
    :param closed: 'left'/'right'/'both'/'neither'
    :param name: 索引名
    """
    if freq is None:
        freq = 1
    if not isinstance(freq, (int, float)) or isinstance(freq, bool):
        raise NotImplementedError("string freq not supported, pass a numeric step")
    if freq == 0:
        raise ValueError("freq must not be 0")
    given = sum(x is not None for x in (start, end, periods, freq))
    if given < 3:
        raise ValueError("at least 3 of start, end, periods, freq are required")
    if start is None:
        start = end - freq * (periods - 1)
    elif end is None:
        end = start + freq * periods
    if periods is None:
        if (end - start) % freq:
            raise ValueError("inferred `periods` must be integer, got fractional")
        periods = int((end - start) / freq)
    if periods < 1:
        raise ValueError("with `freq` given, `periods` must be >= 1")
    breaks = [start + i * freq for i in range(periods + 1)]
    return IntervalIndex.from_breaks(breaks, closed=closed, name=name)


# ============================================================================
# 数组创建函数
# ============================================================================


def array(data, dtype=None, copy: bool = True):
    """创建数组（转发到 rsarray）。"""
    import rsarray as rnp

    return rnp.array(data, dtype=dtype, copy=copy)


# ============================================================================
# 测试入口
# ============================================================================


def test():
    """运行 veloxframe 内置测试（占位符）。"""
    import warnings

    warnings.warn(
        "veloxframe.test() is a placeholder. Use pytest debug/ for tests.",
        UserWarning,
        stacklevel=2,
    )
    return None
