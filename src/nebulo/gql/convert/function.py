from __future__ import annotations

import typing
from functools import lru_cache

from nebulo.gql.alias import Argument, Field, ResolveInfo, String
from nebulo.gql.parse_info import parse_resolve_info
from nebulo.typemap import TypeMapper

if typing.TYPE_CHECKING:
    from nebulo.sql.table_base import TableBase

__all__ = ["function_factory"]


@lru_cache()
def function_factory(sql_function: TableBase):
    gql_args = {
        arg_name: Argument(TypeMapper.sqla_to_gql(arg_sqla_type, String))
        for arg_name, arg_sqla_type in zip(sql_function.arg_names, sql_function.arg_sqla_types)
    }

    return_type = TypeMapper.sqla_to_gql(sql_function.return_sqla_type, String)
    return_type.sql_function = sql_function

    return Field(return_type, args=gql_args, resolve=async_function_resolver, description="")


async def async_function_resolver(_, info: ResolveInfo, **kwargs):
    context = info.context
    database = context["database"]
    tree = parse_resolve_info(info)
    args = tree.args
    sql_function = tree.return_type.sql_function
    query = sql_function.to_executable(args)
    str_result: str = (await database.fetch_one(query=query))
    return str_result[sql_function.name]
