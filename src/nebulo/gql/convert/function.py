from __future__ import annotations

# Replace string with JWT serializer
import typing
from functools import lru_cache

import jwt
from nebulo.gql.alias import Argument, Field, NonNull, ScalarType
from nebulo.gql.convert.column import convert_type
from nebulo.gql.resolver.asynchronous import async_resolver
from nebulo.gql.resolver.synchronous import sync_resolver
from nebulo.sql.composite import CompositeType as SQLACompositeType

if typing.TYPE_CHECKING:
    from nebulo.sql.table_base import TableBase

__all__ = ["function_factory"]


@lru_cache()
def function_factory(sql_function: TableBase, resolve_async: bool = False):
    gql_args = {
        arg_name: Argument(NonNull(convert_type(arg_sqla_type)))
        for arg_name, arg_sqla_type in zip(sql_function.arg_names, sql_function.arg_sqla_types)
    }

    return_type = convert_type(sql_function.return_sqla_type)
    if issubclass(sql_function.return_sqla_type, SQLACompositeType):
        sqla_composite = sql_function.return_sqla_type
        composite_identifier = sqla_composite.pg_schema + "." + sqla_composite.pg_name

        from nebulo.config import Config

        if composite_identifier == Config.JWT_IDENTIFIER:
            return_type = jwt_factory(Config.JWT_SECRET)

    return_type.sql_function = sql_function
    return Field(return_type, args=gql_args, resolve=async_resolver if resolve_async else sync_resolver, description="")


@lru_cache()
def jwt_factory(secret):
    return ScalarType(
        "JWTToken",
        serialize=lambda result: jwt.encode({k: v for k, v in result.items()}, secret, algorithm="HS256").decode(
            "utf-8"
        ),
    )
