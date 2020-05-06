# pylint: disable=unused-argument,invalid-name,line-too-long,unsubscriptable-object
from __future__ import annotations

from typing import Any, List, Optional, Type

from nebulo.exceptions import SQLParseError
from nebulo.sql.sanitize import sanitize
from sqlalchemy import text as sql_text
from sqlalchemy.sql import sqltypes
from sqlalchemy.sql.type_api import TypeEngine


class SQLFunction:
    """A PostgreSQL Function

    INTERNAL USE ONLY
    """

    def __init__(
        self,
        schema: str,
        name: str,
        arg_names: List[Optional[str]],
        arg_pg_types: List[str],
        arg_sqla_types: List[Type[TypeEngine[Any]]],
        return_sqla_type: Type[TypeEngine[Any]],
    ):
        if len(arg_names) != len(arg_sqla_types) != len(arg_pg_types):
            raise SQLParseError("SQLFunction requires same number of arg_names and sqla_types")
        self.schema = schema
        self.name = name
        self.arg_names = arg_names
        self.arg_pg_types = arg_pg_types
        self.arg_sqla_types = arg_sqla_types
        self.return_sqla_type = return_sqla_type

    def to_executable(self, kwargs):

        if len(kwargs) != len(self.arg_names):
            raise SQLParseError(f"Invalid number of parameters for SQLFunction {self.schema}.{self.name}")

        call_sig = ", ".join(
            [f"{sanitize(arg_value)}::{arg_type}" for arg_value, arg_type in zip(kwargs.values(), self.arg_pg_types)]
        )

        executable = sql_text(f"select {self.schema}.{self.name}({call_sig})")
        return executable


def reflect_functions(engine, schema, type_map) -> List[SQLFunction]:
    """Get a list of functions available in the database"""

    # TODO: Support default arguments
    # I haven't been able to find a way to get an array of default args
    # but you can get a function signature including and not including
    # see proargdefaults, pronargdefaults,
    # pg_get_function_identity_arguments, get_function_arguments

    sql = sql_text(
        """
    select
        n.nspname as function_schema,
        p.proname as function_name,
        proargnames arg_names,
        (select array_agg((select typnamespace::regnamespace::text from pg_type where oid=type_oid)) from unnest(proargtypes) x(type_oid)) arg_types_schema,
        (select array_agg(type_oid::regtype::text) from unnest(proargtypes) x(type_oid)) arg_types,
        t.typnamespace::regnamespace::text as return_type_schema,
        t.typname as return_type

    from
        pg_proc p
        left join pg_namespace n on p.pronamespace = n.oid
        left join pg_language l on p.prolang = l.oid
        left join pg_type t on t.oid = p.prorettype
    where
        n.nspname not in ('pg_catalog', 'information_schema')
        and n.nspname like :schema
        """
    )
    rows = engine.execute(sql, schema=schema).fetchall()

    functions: List[SQLFunction] = []

    for (
        func_schema,
        func_name,
        arg_names,
        arg_type_schemas,
        pg_arg_types,
        pg_return_type_schema,
        pg_return_type_name,
    ) in rows:
        arg_names = arg_names or []
        pg_arg_types = pg_arg_types or []
        sqla_arg_types = [
            type_map.get(pg_type_name, sqltypes.NULLTYPE)
            for pg_type_schema, pg_type_name in zip(arg_type_schemas, pg_arg_types) or []
        ]
        sqla_return_type = type_map.get(pg_return_type_name, sqltypes.NULLTYPE)

        function = SQLFunction(
            schema=func_schema,
            name=func_name,
            arg_names=arg_names,
            arg_pg_types=pg_arg_types,
            arg_sqla_types=sqla_arg_types,
            return_sqla_type=sqla_return_type,
        )
        functions.append(function)

    return functions
