from __future__ import annotations

from typing import List, Tuple

from nebulo.sql.reflection.function import SQLFunction, reflect_functions
from nebulo.sql.reflection.names import rename_table, rename_to_many_collection, rename_to_one_collection
from nebulo.sql.reflection.types import reflect_composites
from nebulo.sql.reflection.views import reflect_views
from nebulo.sql.table_base import TableProtocol
from sqlalchemy import MetaData, types
from sqlalchemy.dialects.postgresql import base as pg_base
from sqlalchemy.engine import Engine
from sqlalchemy.ext.automap import automap_base


def reflect_sqla_models(engine: Engine, schema: str = "public") -> Tuple[List[TableProtocol], List[SQLFunction]]:
    """Reflect SQLAlchemy Declarative Models from a database connection"""

    meta = MetaData()
    declarative_base = automap_base(metadata=meta)

    # Register event listeners to apply GQL attr keys to columns

    # Retrive a copy of the full type map
    basic_type_map = pg_base.ischema_names.copy()

    # Reflect composite types (not supported by sqla)
    composites = reflect_composites(engine, schema, basic_type_map)

    # Register composite types with SQLA to make them available during reflection
    pg_base.ischema_names.update({type_name: type_ for (type_schema, type_name), type_ in composites.items()})

    # Retrive a copy of the full type map
    # NOTE: types are not schema namespaced so colisions can occur reflecting tables
    type_map = pg_base.ischema_names.copy()
    type_map["bool"] = types.Boolean  # type: ignore

    # Reflect views as SQLA ORM table
    views = reflect_views(engine=engine, schema=schema, declarative_base=declarative_base)

    declarative_base.prepare(
        engine,
        reflect=True,
        schema=schema,
        classname_for_table=rename_table,
        name_for_scalar_relationship=rename_to_one_collection,
        name_for_collection_relationship=rename_to_many_collection,
    )

    # Register tables as types so functions can return a row of a table
    tables = list(declarative_base.classes) + views
    for table in tables + views:
        type_map[table.__table__.name] = table

    # Reflect functions, allowing composite types
    functions = reflect_functions(engine=engine, schema=schema, type_map=type_map)

    # SQLA Tables
    return (tables, functions)
