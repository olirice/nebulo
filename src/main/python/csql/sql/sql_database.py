from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from csql.sql.table_base import TableBase

from .reflection.functions import get_function_names, reflect_function

if TYPE_CHECKING:
    from csql.user_config import UserConfig


class SQLDatabase:
    def __init__(self, config: UserConfig):
        # Configure SQLAlchemy
        self.engine = create_engine(config.connection, echo=config.echo_queries)
        self.schema = config.schema
        self.base = TableBase
        self.base.prepare(self.engine, reflect=True, schema=config.schema)
        self.session = scoped_session(sessionmaker(bind=self.engine))

        # SQLA Tables
        self.models = list(self.base.classes)

    @property
    @lru_cache()
    def functions(self):
        function_names = get_function_names(self.engine, schema=self.schema)
        # function_names = ["authenticate"]
        reflected_functions = []
        for function_name in function_names:
            ref_fun = reflect_function(self.engine, function_name, schema=self.schema)
            reflected_functions.append(ref_fun)
        return reflected_functions
