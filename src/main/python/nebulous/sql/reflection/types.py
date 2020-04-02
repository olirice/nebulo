"""

Considerations for Composite Types

During reflection, SQLAlchemy's postgres dialect looks up types in
sqlalchemy.dialects.postgresql.base.ischema_names

We query postgres for collect definitions of available composite types and
dynamically produce a type for each. Those types are then registered with
ischema_names to make them available during reflection.

There is a sqlalchemy type for generating composites but they do not support
reflection and are generally clunky to work with. When using sqlalchmy_utils
CompositeType, we must call the register_composites function it provides
to enable psycopg2 to serialize and deserialize them.

The sqla native ARRAY type is not compatible with CompositeType so we also have
to replace it in ischema_names lookup

The current implementation does not support nested composite types because it
would introduce a recursive lookup. This is trivially fixable.

"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql.base import ischema_names
from sqlalchemy.sql.sqltypes import TypeEngine

from sqlalchemy_utils import CompositeArray, CompositeType, register_composites
from stringcase import pascalcase

# Ensure the array type is present
# Its should always be, this is hedging against SQLA changes
ARRAY_KEY = "_array"
assert ARRAY_KEY in ischema_names

# Replace SQLA Postgres ARRAY type with one that is compatible
# with composites so they can be reflected
ischema_names[ARRAY_KEY] = CompositeArray


class TypeRegister:
    """Registers composite types and provides an interface for looking up a type from a
    string name e.g. TypeRegister.get('text') -> sa.TEXT
    """

    def __init__(self, engine, schema=None):
        self.engine = engine
        self.schema = schema or "public"
        self.dialect = self.engine.dialect
        self.domains = self.dialect._load_domains(engine)  # pylint: disable=protected-access
        enum_recs = self.dialect._load_enums(engine)  # pylint: disable=protected-access
        self.enums = dict(
            ((rec["name"],), rec) if rec["visible"] else ((rec["schema"], rec["name"]), rec)
            for rec in enum_recs
        )
        self.composites = self.user_defined_composites()

    def get(self, type_name: str, exclude_user_defined=False) -> TypeEngine:
        """Returns the correct SQLAlchemy type given the SQL type
        as a string"""
        # First try to get a normal SQLAlchemy Type
        result_type = self.dialect._get_column_info(  # pylint: disable=protected-access
            name=None,
            format_type=type_name,
            default=None,
            notnull=False,
            domains=self.domains,
            enums=self.enums,
            schema=self.schema,
            comment=None,
        )["type"]

        # Update to a user defined type if one is available
        # TODO (OR): Update to work recursively (nested composites)
        if not exclude_user_defined:
            result_type = self.composites.get(type_name, result_type)

        return result_type

    @lru_cache()
    def user_defined_composites(self):
        result = self.engine.execute(UDT_SQL_QUERY).fetchall()
        udt = defaultdict(dict)
        for (_, type_name, _, _, attname, _, attnotnull, fulltype, _) in result:
            # TODO(OR): Filter on schema
            udt[type_name][attname] = {"sql_type_name": fulltype, "nullable": not attnotnull}

        registry = {}
        # Create type at runtime
        for user_type, user_type_attrs in udt.items():
            attributes = []
            for udt_attr_name, attrs in user_type_attrs.items():
                attributes.append(
                    sa.Column(
                        udt_attr_name,
                        self.get(attrs["sql_type_name"], exclude_user_defined=True),
                        nullable=attrs["nullable"],
                    )
                )

            # SQLAchemyUtils will autotrack composite types that are defined here

            udt = type(
                pascalcase(user_type),
                (CompositeType,),
                {
                    "__init__": lambda self: super(  # pylint: disable=bad-super-call
                        self.__class__, self
                    ).__init__(
                        user_type, attributes  # pylint: disable=cell-var-from-loop
                    )
                },
            )

            # Instantiate the user define type so SQLA_utils becomes aware of it
            _ = udt()

            # Keep track of it for future lookups
            ischema_names[user_type] = udt
            registry[user_type] = udt

        # Register defined composites with SQLAlchemy so reflection will use them
        with self.engine.connect() as connection:
            register_composites(connection)

        return registry


UDT_SQL_QUERY = """
    with user_defined_types as (
            SELECT
                    n.nspname as schema_name, --text
                    t.typname as type_name, --text
                    typrelid type_id --oid
            FROM
                    pg_type t
                    LEFT JOIN pg_catalog.pg_namespace n
                            ON n.oid = t.typnamespace
            WHERE
                    (t.typrelid = 0 OR (SELECT c.relkind = 'c' FROM pg_catalog.pg_class c WHERE c.oid = t.typrelid))
                    AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_type el WHERE el.oid = t.typelem AND el.typarray = t.oid)
                AND n.nspname NOT IN ('pg_catalog', 'information_schema')
    )

    SELECT
            schema_name, --text
            type_name, --text
            type_id, --oid
            attnum, --smallint
            attname, --text
            attndims, --int
            att.attnotnull, --bool
        format_type(t.oid, att.atttypmod) AS fulltype, --text
        CASE WHEN t.typelem > 0 THEN t.typelem ELSE t.oid END as elemoid --oid
    FROM
            user_defined_types udt
            JOIN pg_attribute att
                    on att.attrelid = udt.type_id
            JOIN pg_type t
                    ON t.oid=atttypid
        JOIN pg_namespace nsp
                    ON t.typnamespace=nsp.oid
        LEFT OUTER JOIN pg_type b
                    ON t.typelem=b.oid
        LEFT OUTER JOIN pg_collation c
                    ON att.attcollation=c.oid
        LEFT OUTER JOIN pg_namespace nspc
                    ON c.collnamespace=nspc.oid
    ORDER by
            schema_name, type_name, attnum;
"""
