"""
A base class to derive sql tables from
"""

from typing import TYPE_CHECKING, Any, Dict, Tuple

from nebulous.sql.computed_column_mixin import ComputedColumnsMixin
from sqlalchemy import Column, MetaData
from sqlalchemy.ext.automap import automap_base

if TYPE_CHECKING:
    _Base = declarative_base()
    ColumnType = Column[Any]  # pylint: disable=unsubscriptable-object,invalid-name
else:
    _Base = object
    ColumnType = Column


def build_base():
    return automap_base(metadata=MetaData())


class TableBase(build_base(), ComputedColumnsMixin):
    """Base class for application sql tables"""

    __abstract__ = True
    __table_args__: Tuple[Any, Any] = ()
    __mapper_args__: Dict[str, Any] = {}
