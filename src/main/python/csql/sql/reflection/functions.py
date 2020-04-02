# pylint: disable=bad-continuation
from typing import List

from sqlalchemy import text
from sqlalchemy.sql.sqltypes import TypeEngine


class SQLFunction:
    """Internal representation of a SQL function"""

    def __init__(
        self,
        func_name: str,
        arg_names: List[str],
        arg_types: List[TypeEngine],
        return_type: TypeEngine,
    ):
        self.func_name = func_name
        self.arg_names = arg_names
        self.arg_types = arg_types
        self.return_type = return_type


def get_function_names(connection, schema: str):

    query = text(
        """
    select routine_name --, specific_name,
    from
        information_schema.routines funcs
    where
        routine_schema = :schema
        and external_language <> 'C'
        and 'USER-DEFINED' <> all(select data_type
                                  from information_schema.parameters
                                  where parameters.specific_name=funcs.specific_name)
    """
    )

    rows = connection.execute(query, {"schema": schema}).fetchall()
    function_names = [x[0] for x in rows]

    return function_names


def reflect_function(connection, function_name: str, schema: str):
    """Connection is an engine"""

    dialect = connection.dialect
    domains = dialect._load_domains(connection)
    enum_recs = dialect._load_enums(connection)
    enums = dict(
        ((rec["name"],), rec) if rec["visible"] else ((rec["schema"], rec["name"]), rec)
        for rec in enum_recs
    )

    # TODO(OR): Make sure sqlite and mysql have the same private function
    def reflect_type(dialect, type_name: str) -> TypeEngine:
        """Returns the correct SQLAlchemy type given the SQL type
        as a string"""
        return dialect._get_column_info(
            name=None,
            format_type=type_name,
            default=None,
            notnull=False,
            domains=domains,
            enums=enums,
            schema=schema,
            comment=None,
        )["type"]

        # User Defined Types

    query = text(
        """
        SELECT
                pg_proc.oid,
                pg_proc.proname sql_func_name,
                CASE
                WHEN pg_proc.proretset
                THEN 'setof ' || pg_catalog.format_type(pg_proc.prorettype, NULL)
                ELSE pg_catalog.format_type(pg_proc.prorettype, NULL)
                END return_type,
                pg_proc.proargnames param_names,
                -- Type name as text
                array(select typname from pg_type, unnest(pg_proc.proargtypes) bc(d) where oid = bc.d) param_types

        FROM pg_catalog.pg_proc
            JOIN pg_catalog.pg_namespace ON (pg_proc.pronamespace = pg_namespace.oid)
            JOIN pg_catalog.pg_language ON (pg_proc.prolang = pg_language.oid)
        WHERE
            pg_proc.prorettype <> 'pg_catalog.cstring'::pg_catalog.regtype
            AND (pg_proc.proargtypes[0] IS NULL
                OR pg_proc.proargtypes[0] <> 'pg_catalog.cstring'::pg_catalog.regtype)

            AND pg_proc.proname ilike :function_name
            AND pg_namespace.nspname = :schema
                and lanname <> 'c'
            AND pg_catalog.pg_function_is_visible(pg_proc.oid);
    """
    )

    oid, sql_func_name, return_type, param_names, param_types = connection.execute(
        query, {"schema": schema, "function_name": function_name}
    ).first()
    param_types = [reflect_type(dialect, x) for x in param_types]
    return_type = reflect_type(return_type)

    sql_function = SQLFunction(
        func_name=sql_func_name,
        arg_names=param_names,
        arg_types=param_types,
        return_type=return_type,
    )

    return sql_function
