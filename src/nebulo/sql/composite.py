from __future__ import annotations

from collections import namedtuple
from typing import TYPE_CHECKING, Any, List, NamedTuple, Type

from sqlalchemy import Column
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.types import TypeDecorator, UserDefinedType

if TYPE_CHECKING:
    ColumnType = Column[Any]
    TypeEngineType = TypeEngine[Any]
else:
    ColumnType = Column
    TypeEngineType = TypeEngine


class CompositeType(UserDefinedType):  # type: ignore
    """
    Represents a PostgreSQL composite type.

    :param name:
        Name of the composite type.
    :param columns:
        List of columns that this composite type consists of
    """

    python_type = tuple

    name: str
    columns: List[ColumnType] = []
    type_cls: Type[NamedTuple]

    def get_col_spec(self):
        return self.name

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            processed_value = []
            for i, column in enumerate(self.columns):
                if isinstance(column.type, TypeDecorator):
                    processed_value.append(column.type.process_bind_param(value[i], dialect))
                else:
                    processed_value.append(value[i])
            return self.type_cls(*processed_value)  # type: ignore

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            cls = value.__class__
            kwargs = {}
            for column in self.columns:
                if isinstance(column.type, TypeDecorator):
                    kwargs[column.name] = column.type.process_result_value(getattr(value, column.name), dialect)
                else:
                    kwargs[column.name] = getattr(value, column.name)
            return cls(**kwargs)

        return process


def composite_type_factory(name: str, columns: List[ColumnType]) -> TypeEngineType:

    for column in columns:
        column.key = column.name

    def init(self, *args, **kwargs):
        pass

    type_cls: Type[NamedTuple] = namedtuple(name, [c.name for c in columns])  # type: ignore

    composite = type(
        name,
        (CompositeType,),
        {"name": name, "columns": columns, "type_cls": type_cls, "__init__": init},  # type:ignore
    )
    return composite  # type: ignore
