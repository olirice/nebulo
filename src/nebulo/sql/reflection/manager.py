from __future__ import annotations

from typing import List, Tuple

from nebulo.sql.reflection.function import SQLFunction, reflect_functions
from nebulo.sql.reflection.utils import (
    rename_columns,
    rename_table,
    rename_to_many_collection,
    rename_to_one_collection,
)
from nebulo.sql.table_base import TableBase
from sqlalchemy.engine import Engine
from nebulo.typemap import TypeMapper
from nebulo.sql.reflection.types import reflect_types, reflect_composites
from sqlalchemy import event, Table
from sqlalchemy.dialects.postgresql import base as pg_base


def reflect_sqla_models(
    engine: Engine, schema: str = "public", declarative_base=TableBase
) -> Tuple[List[TableBase], List[SQLFunction]]:
    """Reflect SQLAlchemy Declarative Models from a database connection"""
    # Register event listeners to apply GQL attr keys to columns


    # Retrive a copy of the full type map
    basic_type_map = pg_base.ischema_names.copy()

    # Reflect composite types (not supported by sqla)
    composites = reflect_composites(engine, schema, basic_type_map)
    # Register compostie types with SQLA to make them available during reflection
    # NOTE: types are not schema namespaced so colisions can occur
    pg_base.ischema_names.update({type_name:  type_ for (type_schema, type_name), type_ in composites.items()})
    # Retrive a copy of the full type map

    type_map = pg_base.ischema_names.copy()
    
    # Reflect functions, allowing composite types
    functions = reflect_functions(engine=engine, schema=schema, type_map=type_map)
    
    # Event listeners impacting reflection
    rename_columns()


    declarative_base.prepare(
        engine,
        reflect=True,
        schema=schema,
        classname_for_table=rename_table,
        #name_for_scalar_relationship=rename_to_one_collection,
        #name_for_collection_relationship=rename_to_many_collection,
    )


    # SQLA Tables
    return (list(declarative_base.classes), functions)
