# pylint: disable=invalid-name,unsubscriptable-object
from __future__ import annotations
from functools import lru_cache

from nebulo.gql.alias import (
    Field,
    NonNull,
    ObjectType,
    InputObjectType,
    InputField,
    CompositeType,
)
from nebulo.text_utils import snake_to_camel

import typing
from collections import namedtuple

from flupy import flu
from nebulo.gql.alias import Boolean, Int, ScalarType, String, Type
from nebulo.sql.reflection.composite import CompositeType as SQLACompositeType
from nebulo.text_utils import snake_to_camel
from sqlalchemy import Column
from sqlalchemy import text as sql_text
from sqlalchemy import types
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.sql.schema import Column

from nebulo.gql.default_resolver import default_resolver

if typing.TYPE_CHECKING:
    from nebulo.sql.table_base import TableBase

    ColumnType = Column[typing.Any]
else:
    ColumnType = Column


UnknownType = ScalarType(name="UnknownString", serialize=str)
DateTimeType = ScalarType(name="DateTime", serialize=str)
DateType = ScalarType(name="Date", serialize=str)
TimeType = ScalarType(name="Time", serialize=str)
UUIDType = ScalarType(name="UUID", serialize=str)
INETType = ScalarType(name="INET", serialize=str)
CIDRType = ScalarType(name="CIDR", serialize=str)


SQLA_TO_GQL = {
    types.Boolean: Boolean,
    # Number
    types.Integer: Int,
    types.INTEGER: Int,
    types.String: String,
    # Text
    types.Text: String,
    types.Unicode: String,
    types.UnicodeText: String,
    # Date
    types.Date: DateType,
    types.Time: TimeType,
    types.DateTime: DateTimeType,
    postgresql.TIMESTAMP: DateTimeType,
    # Other
    postgresql.UUID: UUIDType,
    postgresql.INET: INETType,
    postgresql.CIDR: CIDRType,
}


@lru_cache()
def convert_column(column: ColumnType) -> Field:
    """Converts a sqlalchemy column into a graphql field or input field"""
    sqla_type = type(column.type)
    if issubclass(sqla_type, SQLACompositeType):
        gql_type = composite_factory(sqla_type)
    else:
        gql_type = SQLA_TO_GQL.get(sqla_type, String)

    notnull = not column.nullable
    return_type = NonNull(gql_type) if notnull else gql_type

    return Field(return_type, resolve=default_resolver)


@lru_cache()
def composite_factory(sqla_composite: SQLACompositeType) -> ObjectType:
    def build_composite_column_resolver(column_key):
        def resolver(parent, info, **kwargs):
            return parent[column_key]

        return resolver

    name = snake_to_camel(sqla_composite.name, upper=True)
    fields = {}

    for column in sqla_composite.columns:
        column_key = str(column.key)
        gql_key = column_key
        gql_type = convert_column(column)
        gql_type.resolve = build_composite_column_resolver(str(column.name))
        fields[gql_key] = gql_type

    return_type = CompositeType(name, fields)
    return_type.sqla_composite = sqla_composite
    return return_type


@lru_cache()
def convert_column_to_input(column: ColumnType) -> InputField:
    """Converts a sqlalchemy column into a graphql field or input field"""
    sqla_type = type(column.type)
    if issubclass(sqla_type, SQLACompositeType):
        gql_type = composite_input_factory(sqla_type)
    else:
        gql_type = SQLA_TO_GQL.get(sqla_type, String)

    notnull = not column.nullable
    return_type = NonNull(gql_type) if notnull else gql_type

    return InputField(return_type)


@lru_cache()
def composite_input_factory(sqla_composite: SQLACompositeType) -> ObjectType:
    name = snake_to_camel(sqla_composite.name, upper=True) + "Input"
    fields = {}

    for column in sqla_composite.columns:
        column_key = str(column.key)
        gql_key = column_key
        gql_field = convert_column_to_input(column)
        fields[gql_key] = gql_field

    return_type = InputObjectType(name, fields)
    return_type.sqla_composite = sqla_composite
    return return_type
