from __future__ import annotations

from typing import List

from nebulo.sql.reflection_utils import (
    rename_columns,
    rename_table,
    rename_to_many_collection,
    rename_to_one_collection,
)
from nebulo.sql.table_base import TableBase
from sqlalchemy.engine import Engine


def reflect_sqla_models(engine: Engine, schema: str = "public", declarative_base=TableBase) -> List[TableBase]:
    """Reflect SQLAlchemy Declarative Models from a database connection"""
    # Register event listeners to apply GQL attr keys to columns
    rename_columns()

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
    return list(base.classes)
