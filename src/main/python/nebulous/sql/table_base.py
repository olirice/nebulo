"""
A base class to derive sql tables from
"""

from typing import Any, Dict, Tuple

from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base


def build_base():
    return automap_base(metadata=MetaData())


class TableBase(build_base()):
    """Base class for application sql tables"""

    __abstract__ = True
    __table_args__: Tuple[Any, Any] = ()
    __mapper_args__: Dict[str, Any] = {}
