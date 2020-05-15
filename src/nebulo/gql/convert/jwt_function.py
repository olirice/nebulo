from __future__ import annotations

import typing
from functools import lru_cache

import jwt
from nebulo.gql.alias import Argument, Field, NonNull, ScalarType
from nebulo.gql.convert.column import convert_type
from nebulo.gql.resolver.asynchronous import async_resolver
from nebulo.gql.resolver.synchronous import sync_resolver
from nebulo.sql.composite import CompositeType as SQLACompositeType
from nebulo.sql.reflection.function import SQLFunction

__all__ = ["jwt_function_factory"]


@lru_cache()
def jwt_function_factory(sql_function: SQLFunction, jwt_secret: str, resolve_async: bool = False) -> Field:
    assert issubclass(sql_function.return_sqla_type, SQLACompositeType)

    gql_args = {
        arg_name: Argument(NonNull(convert_type(arg_sqla_type)))
        for arg_name, arg_sqla_type in zip(sql_function.arg_names, sql_function.arg_sqla_types)
    }

    return_type = convert_type(sql_function.return_sqla_type)

    return_type = ScalarType(
        "JWT",
        serialize=lambda result: jwt.encode({k: v for k, v in result.items()}, jwt_secret, algorithm="HS256").decode(
            "utf-8"
        ),
    )

    return_type.sql_function = sql_function
    return Field(return_type, args=gql_args, resolve=async_resolver if resolve_async else sync_resolver, description="")


def is_jwt_function(sql_function: SQLFunction, jwt_identifier: typing.Optional[str]):
    function_return_type_identifier = sql_function.return_pg_type_schema + "." + sql_function.return_pg_type
    return function_return_type_identifier == jwt_identifier
