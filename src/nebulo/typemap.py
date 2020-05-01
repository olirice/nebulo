# pylint: disable=invalid-name
import typing

from nebulo.gql.alias import Int, ScalarType, String, Type
from sqlalchemy import text as sql_text
from sqlalchemy import types
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.sql.type_api import TypeEngine

from flupy import flu

__all__ = ["TypeMapper"]

DateTimeType = ScalarType(name="DateTime", serialize=str)
DateType = ScalarType(name="Date", serialize=str)
TimeType = ScalarType(name="Time", serialize=str)
UUIDType = ScalarType(name="UUID", serialize=str)
INETType = ScalarType(name="INET", serialize=str)
CIDRType = ScalarType(name="CIDR", serialize=str)


class TypeMapper:
    def __init__(self, engine, schema: str = "public"):
        self.engine = engine
        self.dialect: PGDialect = engine.dialect
        self.schema = schema

    _sqla_to_gql = {
        # Number
        types.Integer: Int,
        types.INTEGER: Int,
        types.String: String,
        # Text
        types.Text: String,
        types.Unicode: String,
        types.UnicodeText: String,
        # Date
        types.Date: DateType,
        types.Time: TimeType,
        types.DateTime: DateTimeType,
        postgresql.TIMESTAMP: DateTimeType,
        # Other
        postgresql.UUID: UUIDType,
        postgresql.INET: INETType,
        postgresql.CIDR: CIDRType,
    }

    def name_to_sqla(self, pg_type_name: str) -> TypeEngine:
        """Looks up a SQLA type from its sql name (supports enums)"""
        sqla_type = self.dialect._get_column_info(  # pylint: disable=protected-access
            name=None,
            format_type=pg_type_name,
            default=None,
            notnull=False,
            domains=self.dialect._load_domains(self.engine),
            enums=self.dialect._load_enums(self.engine),
            schema=self.schema,
            comment=None,
        )["type"]
        return sqla_type

    @classmethod
    def sqla_to_gql(cls, sqla_type: TypeEngine, default: Type = String) -> Type:
        """Looks up a GraphQL type from a SQLA"""
        return cls._sqla_to_gql.get(sqla_type, default)

    def reflect_composites(self) -> typing.List:
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
        rows = self.engine.execute(sql, schema=self.schema).fetchall()

        for (full_name, (schema_name, composite_name, column_name, data_type, ordinal, is_required, desc)) in flu(
            rows
        ).group_by(lambda x: x[0] + "." + x[1]):
            pass

        return []
