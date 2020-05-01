# pylint: disable=unused-argument,invalid-name,line-too-long
from __future__ import annotations

from typing import List, Optional

from nebulo.exceptions import SQLParseError
from nebulo.sql.sanitize import sanitize
from nebulo.typemap import TypeMapper
from sqlalchemy import text as sql_text
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
        arg_pg_types: List[TypeEngine],
        arg_sqla_types: List[TypeEngine],
        return_sqla_type: TypeEngine,
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


def reflect_functions(engine, schema="public") -> List[SQLFunction]:
    """Get a list of functions available in the database"""
    sql = sql_text(
        """
    select
        n.nspname as function_schema,
        p.proname as function_name,
        proargnames arg_names,
        (select array_agg(type_oid::regtype::text) from unnest(proargtypes) x(type_oid)) arg_types,
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

    type_mapper = TypeMapper(engine, schema)

    for func_schema, func_name, arg_names, pg_arg_types, pg_return_type_name in rows:
        sqla_arg_types = [type_mapper.name_to_sqla(pg_type_name) for pg_type_name in pg_arg_types]
        sqla_return_type = type_mapper.name_to_sqla(pg_return_type_name)
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
