# pylint: disable=invalid-name,unsubscriptable-object
from __future__ import annotations

import typing
from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import (
    Boolean,
    CompositeType,
    EnumType,
    Field,
    Float,
    InputField,
    InputObjectType,
    Int,
    NonNull,
    ScalarType,
    String,
)
from nebulo.gql.resolve.resolvers.default import default_resolver
from nebulo.sql.composite import CompositeType as SQLACompositeType
from nebulo.sql.table_base import TableProtocol
from nebulo.text_utils import snake_to_camel
from sqlalchemy import Column, types
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.type_api import TypeEngine

UnknownType = ScalarType(name="UnknownString", serialize=str)
DateTimeType = ScalarType(name="DateTime", serialize=str)
DateType = ScalarType(name="Date", serialize=str)
TimeType = ScalarType(name="Time", serialize=str)
UUIDType = ScalarType(name="UUID", serialize=str)
INETType = ScalarType(name="INET", serialize=str)
CIDRType = ScalarType(name="CIDR", serialize=str)


SQLA_TO_GQL = {
    types.Boolean: Boolean,
    # Integer
    types.Integer: Int,
    types.INTEGER: Int,
    types.BIGINT: Int,
    # Float
    types.Float: Float,
    types.Numeric: Float,
    # required b/c json uses 32 bit integers
    types.BigInteger: Float,
    # Text
    types.Text: String,
    types.String: String,
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
def convert_type(sqla_type: TypeEngine):
    type_class = type(sqla_type)

    if issubclass(type_class, SQLACompositeType):
        return composite_factory(type_class)

    if issubclass(type_class, postgresql.base.ENUM):
        return enum_factory(sqla_type)

    if isinstance(sqla_type, TableProtocol):
        from .table import table_factory

        return table_factory(sqla_type)

    # TODO(OR): Enums
    return SQLA_TO_GQL.get(type_class, String)


@lru_cache()
def convert_column(column: Column) -> Field:
    """Converts a sqlalchemy column into a graphql field or input field"""
    gql_type = convert_type(column.type)
    notnull = not column.nullable
    return_type = NonNull(gql_type) if notnull else gql_type
    return Field(return_type, resolve=default_resolver)


@lru_cache()
def enum_factory(sqla_enum: typing.Type[postgresql.base.ENUM]) -> EnumType:
    name = Config.enum_name_mapper(sqla_enum)
    return EnumType(name=name, values={val: val for val in sqla_enum.enums})


@lru_cache()
def composite_factory(sqla_composite: SQLACompositeType) -> CompositeType:
    name = snake_to_camel(sqla_composite.name, upper=True)
    fields = {}

    for column in sqla_composite.columns:
        column_key = str(column.key)
        gql_key = column_key
        gql_type = convert_column(column)
        fields[gql_key] = gql_type

    return_type = CompositeType(name, fields)
    return_type.sqla_composite = sqla_composite
    return return_type


@lru_cache()
def convert_input_type(sqla_type: typing.Type[TypeEngine[typing.Any]]):
    if issubclass(sqla_type, SQLACompositeType):
        gql_type = composite_input_factory(sqla_type)
    else:
        gql_type = SQLA_TO_GQL.get(sqla_type, String)
    return gql_type


@lru_cache()
def convert_column_to_input(column: Column) -> InputField:
    """Converts a sqlalchemy column into a graphql field or input field"""
    sqla_type = type(column.type)
    gql_type = convert_input_type(sqla_type)
    return InputField(gql_type)


@lru_cache()
def composite_input_factory(sqla_composite: SQLACompositeType) -> InputObjectType:
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
