from __future__ import annotations

from collections import namedtuple
from typing import List, NamedTuple, Type

from sqlalchemy import Column
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.types import UserDefinedType


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
    columns: List[Column] = []
    type_cls: Type[NamedTuple]

    pg_name: str
    pg_schema: str

    def init(self, *args, **kwargs):
        pass


def composite_type_factory(name: str, columns: List[Column], pg_name: str, pg_schema: str) -> TypeEngine:

    for column in columns:
        column.key = column.name

    type_cls: Type[NamedTuple] = namedtuple(name, [c.name for c in columns])  # type: ignore

    composite = type(
        name,
        (CompositeType,),
        {
            "name": name,
            "columns": columns,
            "type_cls": type_cls,
            "pg_name": pg_name,
            "pg_schema": pg_schema,
        },  # type:ignore
    )
    return composite  # type: ignore
