from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

if TYPE_CHECKING:
    from csql.user_config import UserConfig

from csql.sql.table_base import TableBase
from functools import lru_cache

from .reflection.functions import get_function_names, reflect_function


class SQLDatabase:
    def __init__(self, config: UserConfig):
        # Configure SQLAlchemy
        self.engine = create_engine(config.connection, echo=config.echo_queries)
        self.base = TableBase
        self.base.prepare(self.engine, reflect=True, schema=config.schema)
        self.session = scoped_session(sessionmaker(bind=self.engine))

        # SQLA Tables
        self.models = list(self.base.classes)


    @property
    @lru_cache()
    def functions(self):
        function_names =  get_function_names(self.engine, schema='public')
        return [reflect_function(self.engine, x) for x in function_names]
