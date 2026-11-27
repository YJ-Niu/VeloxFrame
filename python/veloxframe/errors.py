"""veloxframe.errors - 异常与警告类型。

对齐主流库的 ``pd.errors`` 命名空间，提供解析、合并、选项等场景的
专用异常类，便于用户精确捕获错误类型。
"""

from __future__ import annotations


class AbstractMethodWarning(Warning):
    """抽象方法警告：该方法的实现依赖具体子类。"""


class ClosedFileError(ValueError):
    """文件已关闭：对已关闭的文件对象进行读写。"""


class DataError(Exception):
    """数据错误：聚合/查询时列不存在或类型不符。"""


class DtypeWarning(Warning):
    """dtype 转换警告：例如字符串转数值时发生截断/丢弃。"""


class EmptyDataError(ValueError):
    """空数据错误：例如读取仅含表头或完全为空的 CSV。"""


class IncompatibleFrameValue(ValueError):
    """列值与已有 DataFrame 不兼容。"""


class IncompatibilityWarning(UserWarning):
    """版本轻微不兼容警告。"""


class MergeError(ValueError):
    """merge 操作错误：键冲突、列缺失等。"""


class MissingData(Exception):
    """缺失数据错误。"""


class OutOfBoundsDatetime(ValueError):
    """datetime 值超出表示范围。"""


class ParserError(Exception):
    """解析错误：CSV/JSON 等格式解析失败。"""


class PerformanceWarning(UserWarning):
    """性能警告：操作复杂度高于预期。"""


class SettingWithCopyError(ValueError):
    """SettingWithCopy 场景：对切片修改可能无效。"""


class DatabaseError(IOError):
    """数据库操作错误。"""


class OptionError(ValueError):
    """非法选项：set_option 使用了未知/不匹配的选项名。"""


class UnsortedIndexError(KeyError):
    """索引未排序：需要有序索引的操作遇到无序索引。"""


__all__ = [
    "AbstractMethodWarning",
    "ClosedFileError",
    "DataError",
    "DtypeWarning",
    "EmptyDataError",
    "IncompatibleFrameValue",
    "IncompatibilityWarning",
    "MergeError",
    "MissingData",
    "OutOfBoundsDatetime",
    "ParserError",
    "PerformanceWarning",
    "SettingWithCopyError",
    "DatabaseError",
    "OptionError",
    "UnsortedIndexError",
]
