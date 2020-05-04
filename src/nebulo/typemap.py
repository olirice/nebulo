# pylint: disable=invalid-name
import typing
from collections import namedtuple

from flupy import flu
from nebulo.gql.alias import Boolean, Int, ScalarType, String, Type
from nebulo.gql.convert.composite import composite_factory
from nebulo.sql.reflection.composite import CompositeType
from nebulo.text_utils import snake_to_camel
from sqlalchemy import Column
from sqlalchemy import text as sql_text
from sqlalchemy import types
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.orm import CompositeProperty, composite
from sqlalchemy.sql.type_api import TypeEngine

__all__ = ["TypeMapper"]

UnknownType = ScalarType(name="UnknownString", serialize=str)
DateTimeType = ScalarType(name="DateTime", serialize=str)
DateType = ScalarType(name="Date", serialize=str)
TimeType = ScalarType(name="Time", serialize=str)
UUIDType = ScalarType(name="UUID", serialize=str)
INETType = ScalarType(name="INET", serialize=str)
CIDRType = ScalarType(name="CIDR", serialize=str)


class TypeMapper:
    def __init__(self, engine, schema: str = "public"):
        self.engine = engine
        self.dialect: PGDialect = engine.dialect
        self.schema = schema

    _sqla_to_gql = {
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

    _composites = {}


    @classmethod
    def sqla_to_gql(cls, sqla_type: TypeEngine, default: Type = String) -> Type:


        """Looks up a GraphQL type from a SQLA"""
        if issubclass(sqla_type, CompositeType):
            return composite_factory(sqla_type)
        
        return cls._sqla_to_gql.get(sqla_type, default)
