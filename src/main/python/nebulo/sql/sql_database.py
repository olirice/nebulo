from __future__ import annotations

from typing import Optional

from nebulo.sql.table_base import TableBase
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .reflection_utils import rename_columns, rename_table, rename_to_many_collection, rename_to_one_collection


class SQLDatabase:
    def __init__(self, connection: str, schema: str, echo_queries=False, engine: Optional[Engine] = None) -> None:
        # Configure SQLAlchemy
        if engine:
            self.engine = engine
        else:
            self.engine = create_engine(connection, echo=echo_queries)

        self.session = scoped_session(sessionmaker(bind=self.engine))

        # Register event listeners to apply GQL attr keys to columns
        rename_columns()

        self.schema = schema
        self.base = TableBase
        self.base.prepare(
            self.engine,
            reflect=True,
            schema=schema,
            classname_for_table=rename_table,
            name_for_scalar_relationship=rename_to_one_collection,
            name_for_collection_relationship=rename_to_many_collection,
        )

        # SQLA Tables
        self.models = self.base.classes
