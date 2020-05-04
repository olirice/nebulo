# pylint: disable=invalid-name
from typing import Dict, Tuple, List
from collections import namedtuple

from flupy import flu
from nebulo.gql.alias import Boolean, Int, ScalarType, String, Type
from nebulo.text_utils import snake_to_camel
from sqlalchemy import Column
from sqlalchemy import text as sql_text
from sqlalchemy import types
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.orm import CompositeProperty, composite
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.sql import sqltypes
from sqlalchemy import exc as sa_exc
import warnings


def reflect_types(engine, schema="public") -> Dict[Tuple[str,str], TypeEngine]:

    query = sql_text("""
    SELECT
        n.nspname schema_name,
        pg_catalog.format_type ( t.oid, NULL ) AS type_name,
        CASE
            WHEN t.typrelid != 0 THEN CAST ( 'tuple' AS pg_catalog.text )
            WHEN t.typlen < 0 THEN CAST ( 'var' AS pg_catalog.text )
            ELSE CAST ( t.typlen AS pg_catalog.text )
            END AS object_type,
        coalesce ( pg_catalog.obj_description ( t.oid, 'pg_type' ), '' ) AS description
    FROM
        pg_catalog.pg_type t
        JOIN pg_catalog.pg_namespace n
            ON n.oid = t.typnamespace
    WHERE 
        n.nspname in ('pg_catalog', :schema)
    """)
    rows = engine.execute(query, schema= schema).fetchall()


    dialect = engine.dialect
    enums = dialect._load_enums(engine)
    domains = dialect._load_domains(engine)

    def get_default_sqla_type(type_name, type_schema):
        sqla_type = dialect._get_column_info(  # pylint: disable=protected-access
                name=None,
                format_type=type_name, 
                default=None,
                notnull=False,
                domains=domains,
                enums=enums,
                schema=type_schema,
                comment=None,
         )["type"]
        return sqla_type

    
    type_map = {}
    for type_schema, type_name, object_type, description in rows:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=sa_exc.SAWarning)
            sqla_type = get_default_sqla_type(type_name, type_schema)
        if sqla_type != sqltypes.NULLTYPE:
            type_map[(type_schema, type_name)] = sqla_type

    # Collect composites
    composite_type_map = reflect_composites(engine, schema, type_map)
    return {**type_map, **composite_type_map}





def reflect_composites(engine, schema, type_map) -> List:
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

    composites = {}

    for _, composite_rows in flu(rows).group_by(lambda x: x[0] + "." + x[1]):
        # attributed for python class
        attrs = []
        # columns for sqla composite
        columns = []
        for (
            schema_name,
            composite_name,
            column_name,
            data_type,
            _,  # ordinal
            is_required,
            desc,
        ) in composite_rows:
            attrs.append(column_name)
            column_type = type_map.get(data_type, sqltypes.NULLTYPE)
            nullable = not is_required
            column = Column(
                name=column_name,
                key=column_name,
                type_=column_type,
                nullable=nullable,
                comment=desc,
            )
            columns.append(column)
        
        from .composite import CompositeType, CompositeElement, composite_type_factory
        py_composite_name = snake_to_camel(composite_name, upper=True)
        #sqla_composite = CompositeType(py_composite_name, columns)
        sqla_composite = composite_type_factory(py_composite_name, columns)
        composites[(schema_name, composite_name)] = sqla_composite



    return composites




























