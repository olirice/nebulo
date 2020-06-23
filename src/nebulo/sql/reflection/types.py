# pylint: disable=invalid-name
from typing import Dict, Tuple

from flupy import flu
from nebulo.sql.composite import composite_type_factory
from nebulo.text_utils import snake_to_camel
from sqlalchemy import Column
from sqlalchemy import text as sql_text
from sqlalchemy.sql import sqltypes
from sqlalchemy.sql.type_api import TypeEngine


def reflect_composites(engine, schema, type_map) -> Dict[Tuple[str, str], TypeEngine]:
    """Get a list of functions available in the database"""

    sql = sql_text(
        """
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
            /*
            When the schema is public, pg_catalog.format_type does not
            include a schema prefix, but when its any other schema, it does.
            This function removes the schema prefix if it exists for
            consistency
            */
            (
                string_to_array(
                    pg_catalog.format_type ( t.oid, NULL ),
                    '.'
                )
            )[array_upper(
                string_to_array(
                    pg_catalog.format_type ( t.oid, NULL ),
                    '.'
                ),
                1)
            ] as obj_name,
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

    composites = {}

    for _, composite_rows in flu(rows).group_by(lambda x: x[0] + "." + x[1]):
        # attributed for python class
        attrs = []
        # columns for sqla composite
        columns = []
        for (schema_name, composite_name, column_name, data_type, _, is_required, desc) in composite_rows:  # ordinal
            attrs.append(column_name)
            column_type = type_map.get(data_type, sqltypes.NULLTYPE)
            nullable = not is_required
            column = Column(name=column_name, key=column_name, type_=column_type, nullable=nullable, comment=desc)
            columns.append(column)

        py_composite_name = snake_to_camel(composite_name, upper=True)
        # sqla_composite = CompositeType(py_composite_name, columns)
        sqla_composite = composite_type_factory(py_composite_name, columns, composite_name, schema_name)
        composites[(schema_name, composite_name)] = sqla_composite
    return composites
