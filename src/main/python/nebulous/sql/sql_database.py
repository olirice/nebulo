from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from nebulous.sql.table_base import TableBase

from .reflection.functions import get_function_names, reflect_function
from .reflection_utils import (
    rename_columns,
    rename_table,
    rename_to_many_collection,
    rename_to_one_collection,
)

if TYPE_CHECKING:
    from nebulous.user_config import UserConfig


class SQLDatabase:
    def __init__(self, config: UserConfig, engine: None = None) -> None:
        # Configure SQLAlchemy
        if engine:
            self.engine = engine
        else:
            self.engine = create_engine(config.connection, echo=config.echo_queries)

        self.session = scoped_session(sessionmaker(bind=self.engine))

        if config.demo:
            self.build_demo_schema()

        # Type reflector can take a string and return the correct sql column type for sqla
        # It also functions with (non-nested) composites, which sqla proper does not
        # self.type_register = TypeRegister(self.engine, schema=config.schema)

        rename_columns()

        self.schema = config.schema
        self.base = TableBase
        self.base.prepare(
            self.engine,
            reflect=True,
            schema=config.schema,
            classname_for_table=rename_table,
            name_for_scalar_relationship=rename_to_one_collection,
            name_for_collection_relationship=rename_to_many_collection,
        )
        # SQLA Tables
        self.models = self.base.classes

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

    def build_demo_schema(self) -> None:
        self.session.execute(
            """
            DROP SCHEMA public CASCADE;
            CREATE SCHEMA public;
            GRANT ALL ON SCHEMA public TO postgres;
        """
        )

        self.session.execute(
            """
            CREATE TABLE account (
                id serial primary key,
                name text not null,
                created_at timestamp without time zone default (now() at time zone 'utc')
            );

            INSERT INTO account (id, name) VALUES
            (1, 'oliver'),
            (2, 'rachel'),
            (3, 'sophie'),
            (4, 'buddy');


            create table offer (
                id serial primary key, --integer primary key autoincrement,
                currency text,
                account_id int not null,

                constraint fk_offer_account_id
                    foreign key (account_id)
                    references account (id)
            );

            INSERT INTO offer (currency, account_id) VALUES
            ('usd', 2),
            ('gbp', 2),
            ('eur', 3),
            ('jpy', 4);
        """
        )
        self.session.commit()
        return
