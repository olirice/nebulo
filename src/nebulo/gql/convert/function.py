from __future__ import annotations

import typing
from functools import lru_cache

from nebulo.gql.alias import Argument, Field, NonNull
from nebulo.gql.convert.column import convert_type
from nebulo.gql.resolvers import async_resolver, sync_resolver

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
    return_type.sql_function = sql_function

    return Field(return_type, args=gql_args, resolve=async_resolver if resolve_async else sync_resolver, description="")
