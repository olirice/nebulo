# pylint: disable=unused-argument,invalid-name,line-too-long
from __future__ import annotations

from typing import List, Optional

from nebulo.exceptions import SQLParseError
from nebulo.sql.sanitize import sanitize
from nebulo.typemap import TypeMapper
from sqlalchemy import func
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.sql.type_api import TypeEngine

from flupy import flu
from parse import parse


def reflect_composites(engine, schema="public") -> List[SQLFunction]:

    """Get a list of functions available in the database"""
    sql = sql_text("""
WITH types AS (
    SELECT
        n.nspname,
        pg_catalog.format_type ( t.oid, NULL ) AS obj_name,
        CASE
            WHEN t.typrelid != 0 THEN CAST ( 'tuple' AS pg_catalog.text )
            WHEN t.typlen < 0 THEN CAST ( 'var' AS pg_catalog.text )
            ELSE CAST ( t.typlen AS pg_catalog.text )
            END AS obj_type,
        coalesce ( pg_catalog.obj_description ( t.oid, 'pg_type' ), '' ) AS description
    FROM
        pg_catalog.pg_type t
        JOIN pg_catalog.pg_namespace n
            ON n.oid = t.typnamespace
    WHERE ( t.typrelid = 0
            OR ( SELECT c.relkind = 'c'
                    FROM pg_catalog.pg_class c
                    WHERE c.oid = t.typrelid ) )
        AND NOT EXISTS (
                SELECT 1
                    FROM pg_catalog.pg_type el
                    WHERE el.oid = t.typelem
                    AND el.typarray = t.oid )
        AND n.nspname <> 'pg_catalog'
        AND n.nspname <> 'information_schema'
        AND n.nspname !~ '^pg_toast'
),
cols AS (
    SELECT n.nspname::text AS schema_name,
            pg_catalog.format_type ( t.oid, NULL ) AS obj_name,
            a.attname::text AS column_name,
            pg_catalog.format_type ( a.atttypid, a.atttypmod ) AS data_type,
            a.attnotnull AS is_required,
            a.attnum AS ordinal_position,
            pg_catalog.col_description ( a.attrelid, a.attnum ) AS description
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_type t
            ON a.attrelid = t.typrelid
        JOIN pg_catalog.pg_namespace n
            ON ( n.oid = t.typnamespace )
        JOIN types
            ON ( types.nspname = n.nspname
                AND types.obj_name = pg_catalog.format_type ( t.oid, NULL ) )
        WHERE a.attnum > 0
            AND NOT a.attisdropped
)
SELECT
    cols.schema_name,
    cols.obj_name,
    cols.column_name,
    cols.data_type,
    cols.ordinal_position,
    cols.is_required,
    coalesce ( cols.description, '' ) AS description
    FROM
        cols
    WHERE
        cols.schema_name = :schema
    ORDER BY
        cols.schema_name,
        cols.obj_name,
        cols.ordinal_position
    """
    )
    rows = engine.execute(sql, schema=schema).fetchall()

    for composite_full_name
    for full_name, (schema_name, composite_name, column_name, data_type, ordinal, _) in flu(rows).groupby(lambda x: x[0]+'.'+x[1]):





    functions: List[SQLFunction] = []

    type_mapper = TypeMapper(engine, schema)

    for func_schema, func_name, arg_names, pg_arg_types, pg_return_type_name in rows:
        sqla_arg_types = [
            type_mapper.name_to_sqla(pg_type_name) for pg_type_name in pg_arg_types
        ]
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
