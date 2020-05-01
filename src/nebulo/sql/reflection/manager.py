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
from nebulo.sql.reflection.types import reflect_types
from sqlalchemy import event, Table


def reflect_sqla_models(
    engine: Engine, schema: str = "public", declarative_base=TableBase
) -> Tuple[List[TableBase], List[SQLFunction]]:
    """Reflect SQLAlchemy Declarative Models from a database connection"""
    # Register event listeners to apply GQL attr keys to columns

    type_map = reflect_types(engine, schema)

    functions = reflect_functions(engine=engine, schema=schema, type_map=type_map)
    
    # Event listeners impacting reflection
    rename_columns()

    # TODO: Reflect tables with composite types

    base = declarative_base

    base.prepare(
        engine,
        reflect=True,
        schema=schema,
        classname_for_table=rename_table,
        name_for_scalar_relationship=rename_to_one_collection,
        name_for_collection_relationship=rename_to_many_collection,
    )

    # SQLA Tables
    return (list(base.classes), functions)
