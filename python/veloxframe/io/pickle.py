"""Pickle 读写：read_pickle / to_pickle

由 veloxframe/io.py 拆分而来，向后兼容通过 :mod:`veloxframe.io` 包入口保证。
"""

from __future__ import annotations

from ..dataframe import DataFrame
from ..series import Series  # noqa: F401  # 部分函数需要

import pickle as _pickle


def read_pickle(path: str, **kwargs):
    """从 Pickle 文件读取 DataFrame 或 Series。

    Parameters
    ----------
    path : str
        Pickle 文件路径。
    **kwargs
        传递给 pickle.load 的其他参数。

    Returns
    -------
    DataFrame 或 Series
    """
    with open(path, "rb") as f:
        obj = _pickle.load(f)
    if isinstance(obj, dict):
        if obj.get("kind") == "series":
            return Series(
                obj["data"],
                index=obj["index"],
                name=obj["name"],
                dtype=obj["dtype"],
            )
        if "columns" in obj and "data" in obj:
            return DataFrame(obj["data"], columns=obj["columns"])
    if isinstance(obj, DataFrame):
        return obj
    if isinstance(obj, Series):
        return obj
    raise TypeError(f"Pickle file contains {type(obj).__name__}, not DataFrame/Series")


def to_pickle(obj, path: str, **kwargs) -> None:
    """将 DataFrame 或 Series 写入 Pickle 文件。

    Parameters
    ----------
    obj : DataFrame 或 Series
        要写入的对象。
    path : str
        输出文件路径。
    **kwargs
        传递给 pickle.dump 的其他参数。
    """
    # 序列化为纯 Python dict 以避免 pickle Rust 对象
    if isinstance(obj, Series):
        state = {
            "kind": "series",
            "name": obj.name,
            "index": list(obj._index)
            if obj._index is not None
            else list(range(len(obj))),
            "data": list(obj.values),
            "dtype": obj.dtype,
        }
    else:
        state = {
            "columns": list(obj.columns),
            "data": obj.values,
        }
    with open(path, "wb") as f:
        _pickle.dump(state, f, **kwargs)


# ============================================================================
# SQL
# ============================================================================
