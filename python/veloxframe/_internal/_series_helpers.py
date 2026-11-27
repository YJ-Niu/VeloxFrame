"""Series 内部辅助函数与工具类

由 veloxframe/series.py 拆分而来。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional, Union

from ..veloxframe import _DataFrame as _PyDataFrame  # type: ignore
from ..veloxframe import _Series as _PySeries  # type: ignore

if TYPE_CHECKING:
    from ..series import Series  # noqa: F401  # 类型注解使用


def _is_missing(v) -> bool:
    """判断值是否为缺失 (None 或 NaN)。"""
    if v is None:
        return True
    try:
        return v != v  # type: ignore[operator]
    except TypeError:
        return False


class _AlignmentResult(tuple):
    """align() 返回结果，在 repr 中逗号后自动换行，与 主流库 格式一致。"""

    def __repr__(self) -> str:
        if len(self) != 2:
            return super().__repr__()

        left = repr(self[0])
        right = repr(self[1])

        if "\n" in left or "\n" in right:
            return f"({left},\n {right})"

        return f"({left}, {right})"


class _DtypeScalar:
    """带 dtype 属性的标量包装，模拟 rsarray 标量的行为。

    允许标量值通过 .dtype 访问类型信息，如 主流库 的 np.float64(1.0).dtype。
    """

    def __init__(self, value, dtype: str = "float64"):
        self._value = value
        self._dtype = dtype

    @property
    def dtype(self) -> str:
        return self._dtype

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __eq__(self, other) -> bool:
        if isinstance(other, _DtypeScalar):
            return self._value == other._value
        return self._value == other

    def __hash__(self) -> int:
        return hash(self._value)

    def __lt__(self, other) -> bool:
        if isinstance(other, _DtypeScalar):
            return self._value < other._value
        return self._value < other

    def __gt__(self, other) -> bool:
        if isinstance(other, _DtypeScalar):
            return self._value > other._value
        return self._value > other

    def __le__(self, other) -> bool:
        if isinstance(other, _DtypeScalar):
            return self._value <= other._value
        return self._value <= other

    def __ge__(self, other) -> bool:
        if isinstance(other, _DtypeScalar):
            return self._value >= other._value
        return self._value >= other

    def __add__(self, other):
        ov = other._value if isinstance(other, _DtypeScalar) else other
        return self._value + ov

    def __sub__(self, other):
        ov = other._value if isinstance(other, _DtypeScalar) else other
        return self._value - ov

    def __mul__(self, other):
        ov = other._value if isinstance(other, _DtypeScalar) else other
        return self._value * ov

    def __truediv__(self, other):
        ov = other._value if isinstance(other, _DtypeScalar) else other
        return self._value / ov

    def __neg__(self):
        return -self._value

    def __pos__(self):
        return +self._value

    def __abs__(self):
        return abs(self._value)

    def __getattr__(self, name):
        """代理到包装的原始值，使标量可访问其属性（如 Period.freq / datetime.year）。

        仅当 _DtypeScalar 自身没有该属性时才触发（避免影响 dtype/比较等已定义行为）。
        下划线开头的私有属性不代理，防止内部字段泄漏。
        """
        if name.startswith("_"):
            raise AttributeError(f"_DtypeScalar object has no attribute {name!r}")
        return getattr(self._value, name)


def _dtype_to_str(dtype) -> str:
    """将 dtype 参数（str/type 对象/rsarray dtype 对象）规范化为字符串。

    - str 直接返回
    - Python type（如 bool/int/float/str）取 __name__
    - rsarray dtype 对象（如 np.uint8, np.float32）取对应的字符串
    """
    if isinstance(dtype, str):
        return dtype
    # rsarray dtype 对象（如 np.float32, np.uint8）有 __name__ 属性
    if hasattr(dtype, "__name__"):
        name = dtype.__name__.lower()
        # np.bool_ -> bool
        if name == "bool_":
            return "bool"
        return name
    # rsarray dtype 实例（如 dtype('float32')）
    if hasattr(dtype, "name"):
        return str(dtype.name).lower()
    return str(dtype).lower()


def _is_safe_astype(src_dtype: str, target: str) -> bool:
    """判断 astype 转换是否"安全"。

    安全的转换指 Rust 层执行时不会静默产生新的 None 值，
    行为与 Python 层 ``int(v)`` / ``float(v)`` / ``bool(v)`` / ``str(v)`` 一致。

    不安全的转换（如 string -> int / float / bool、float -> int）涉及解析或
    截断，可能在 Python 层抛出 ValueError/TypeError，而 Rust 层静默返回 None。
    为保留 Python 的 raise 行为，此类转换回退到 Python 实现。
    """
    s = src_dtype.lower()
    t = target.lower()
    if s == t:
        return True
    # int/uint 源：所有数值/bool/字符串转换都安全（不会失败）
    if s.startswith("int") or s.startswith("uint"):
        return (
            t.startswith("int")
            or t.startswith("uint")
            or t.startswith("float")
            or t == "bool"
            or t in ("object", "str", "string")
        )
    # float 源：-> float / bool / str 安全；-> int 不安全（NaN/inf 在 Python 会抛错）
    if s.startswith("float"):
        return t.startswith("float") or t == "bool" or t in ("object", "str", "string")
    # bool 源：所有目标都安全
    if s == "bool":
        return True
    # string/object 源：仅 -> string/object 安全；解析数值/bool 不安全
    if s in ("object", "str", "string"):
        return t in ("object", "str", "string")
    # 其他（category / datetime64 / timedelta64 等）：保守起见返回 False
    return False


def _infer_dtype(values: list) -> str:
    """根据数据推断 dtype（对齐 主流库 的行为）。"""
    if not values:
        return "object"

    has_non_null = False
    all_bool = True
    all_int = True
    all_float_or_int = True  # int 或 float 混合时仍视为 float64
    all_str = True

    for v in values:
        if v is None:
            continue
        has_non_null = True
        # bool 优先于 int（True/False is int in Python）
        if isinstance(v, bool):
            all_int = False
            all_float_or_int = False
            all_str = False
        elif isinstance(v, int):
            all_bool = False
            all_str = False
            # all_int 保持 True，但 all_float_or_int 也保持 True（int 可被 float 兼容）
        elif isinstance(v, float):
            all_bool = False
            all_int = False
            all_str = False
            # all_float_or_int 保持 True
        elif isinstance(v, str):
            all_bool = False
            all_int = False
            all_float_or_int = False
        else:
            # 不支持类型 -> object
            all_bool = False
            all_int = False
            all_float_or_int = False
            all_str = False
            return "object"

    # 全 None -> object
    if not has_non_null:
        return "object"
    if all_bool:
        return "bool"
    if all_int:
        return "int64"
    if all_float_or_int:
        return "float64"
    if all_str:
        return "str"
    return "object"


def _format_timedelta(td: timedelta) -> str:
    """将 timedelta 格式化为字符串显示（与 主流库 一致）。

    格式: "N days HH:MM:SS" (天数>0) 或 "HH:MM:SS" (天数为0)
    """
    if td is None:
        return None
    total_seconds = int(td.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    microseconds = td.microseconds
    if days > 0:
        if microseconds > 0:
            return f"{days} days {hours:02d}:{minutes:02d}:{seconds:02d}.{microseconds:06d}"
        return f"{days} days {hours:02d}:{minutes:02d}:{seconds:02d}"
    if microseconds > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{microseconds:06d}"
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _to_python_list(data: Any) -> list:
    """将输入标准化为 Python list。

    对 datetime/date 元素转换为 ISO 字符串（Rust 端不支持 Python datetime 对象）。
    """
    from .._datetime import DatetimeSeries, _to_iso  # 延迟 import 避免循环引用

    def _convert_value(v):
        """将单个值转换为可存储的 Python 类型。

        仅 datetime/timedelta 需要转换，其他类型直接返回。
        先检查 datetime/timedelta，非此类值仅需 1 次 isinstance 即可返回。
        """
        if isinstance(v, (datetime, date, timedelta)):
            if isinstance(v, bool):
                return v
            if isinstance(v, timedelta):
                return _format_timedelta(v)
            return _to_iso(v)
        return v

    if isinstance(data, DatetimeSeries):
        return list(data._inner.values)  # ISO 字符串
    if isinstance(data, _PySeries):
        return list(data.values)
    if isinstance(data, (list, tuple)):
        return [_convert_value(v) for v in data]
    if isinstance(data, dict):
        # dict: 默认用 values
        return list(data.values())
    if hasattr(data, "tolist"):
        raw = data.tolist()
        return [_convert_value(v) for v in raw]
    if data is None:
        return []
    if hasattr(data, "__iter__"):
        out = list(data)
        return [_convert_value(v) for v in out]
    raise TypeError(f"Cannot convert {type(data).__name__} to Series")


def _to_python_list_and_index(data: Any, index=None):
    """将输入标准化为 (values, index)。

    当 data 是 dict 且指定了 index 时，按 index 顺序查找 dict 值，
    缺失的索引对应 None。
    """
    from .._datetime import DatetimeSeries, _to_iso

    def _conv(values):
        return [
            (
                _to_iso(v)
                if isinstance(v, (datetime, date)) and not isinstance(v, bool)
                else v
            )
            for v in values
        ]

    if isinstance(data, DatetimeSeries):
        values = list(data._inner.values)
        idx = list(data._index) if data._index is not None else None
        return values, idx
    if isinstance(data, _PySeries):
        return list(data.values), None
    if isinstance(data, (list, tuple)):
        return _conv(list(data)), None
    if isinstance(data, dict):
        if index is not None:
            # 按指定 index 顺序取 dict 值，缺失的填 None
            idx_list = list(index) if not isinstance(index, list) else index
            values = [data.get(k, None) for k in idx_list]
            return _conv(values), idx_list
        return _conv(list(data.values())), list(data.keys())
    if hasattr(data, "tolist"):
        return _conv(data.tolist()), None
    if data is None:
        return [], None
    raise TypeError(f"Cannot convert {type(data).__name__} to Series")


def _is_range_index(index) -> bool:
    """判断 index 是否为默认的 RangeIndex (0, 1, 2, ...)。"""
    if not index:
        return True
    return list(index) == list(range(len(index)))


# ---------------------------------------------------------------------------
# Series
# ---------------------------------------------------------------------------


def _PySeries_filter(inner: _PySeries, mask: list) -> _PySeries:
    """辅助函数：调用 Rust 端 filter。"""
    return inner.filter(mask)


# ---------------------------------------------------------------------------
# 扩展数组类 (对齐 主流库 ExtensionArray 显示)
# ---------------------------------------------------------------------------


class _ExtensionArray:
    """包装 rsarray ndarray，提供与 主流库 ExtensionArray 相同的显示格式。"""

    def __init__(self, data, dtype_str=None):
        self._data = data
        self._dtype = dtype_str or "float64"

    def __repr__(self) -> str:
        import rsarray as rnp

        arr = rnp.array(self._data)
        # 如果是二维数组 (1, n)，squeeze 成一维
        if arr.ndim > 1:
            arr = arr.squeeze()
        # 使用 rsarray 的 array2string，用逗号分隔，匹配 主流库 格式
        # 主流库 使用 float64 的完整精度（约 16 位），所以指定 precision=16
        values_str = rnp.array2string(
            arr, separator=", ", prefix=" ", suffix="", precision=16
        )
        # array2string 返回的字符串已包含方括号，直接使用
        if values_str.startswith("["):
            values_with_brackets = values_str
        else:
            values_with_brackets = f"[{values_str}]"
        return (
            f"<ExtensionArray>\n"
            f"{values_with_brackets}\n"
            f"Length: {len(arr)}, dtype: {self._dtype}"
        )

    def __len__(self):
        return len(self._data)

    def __getitem__(self, idx):
        return self._data[idx]

    def __array__(self, dtype=None):
        import rsarray as rnp

        return rnp.array(self._data, dtype=dtype)


# ---------------------------------------------------------------------------
# 窗口函数类 (v1.0.0)
# ---------------------------------------------------------------------------
