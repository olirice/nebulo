from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from nebulous.sql.table_base import TableBase

from .reflection.functions import get_function_names, reflect_function

if TYPE_CHECKING:
    from nebulous.user_config import UserConfig


class SQLDatabase:
    def __init__(self, config: UserConfig):
        # Configure SQLAlchemy
        self.engine = create_engine(config.connection, echo=config.echo_queries)
        self.session = scoped_session(sessionmaker(bind=self.engine))

        if config.demo:
            self.build_demo_schema()

        # Type reflector can take a string and return the correct sql column type for sqla
        # It also functions with (non-nested) composites, which sqla proper does not
        # self.type_register = TypeRegister(self.engine, schema=config.schema)

        self.schema = config.schema
        self.base = TableBase
        self.base.prepare(self.engine, reflect=True, schema=config.schema)
        # Meta.reflect(self.engine, schema=self.schema)

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

    def build_demo_schema(self):
        self.session.execute(
            """
        drop table if exists offer;
        """
        )

        self.session.execute(
            """
        drop table if exists account;
        """
        )

        self.session.execute(
            """
        drop table if exists organization;
        """
        )

        self.session.execute(
            """
        create table organization (
            id serial primary key, --integer primary key autoincrement,
            org_name text not null
        );
            """
        )

        self.session.execute(
            """
        create table account (
            id serial primary key, --integer primary key autoincrement,
            name text not null,
            age int,
            organization_id int,

            constraint fk_account_organizationunt_id
                foreign key (organization_id)
                references organization (id)
        );
        """
        )

        self.session.execute(
            """
        create table offer (
            id serial primary key, --integer primary key autoincrement,
            currency text,
            account_id int not null,
            created_at timestamp  not null,

            constraint fk_offer_account_id
                foreign key (account_id)
                references account (id)
        );
        """
        )

        self.session.execute(
            """
        insert into organization (id, org_name) values
            (default, 'oli_corp');
        """
        )

        self.session.execute(
            """
        insert into account (id, name, age, organization_id) values
            (1, 'oliver', 29, 1),
            (2, 'rachel', 29, 1),
            (3, 'buddy', 20, 1)
        ;
        """
        )

        self.session.execute(
            """
        insert into offer (id, currency, account_id, created_at) values
            (1, 'abc', 1, now()),
            (2, 'def', 1, now()),
            (3, 'pqr', 2, now()),
            (4, 'mno', 2, now()),
            (5, 'pqr', 3, now())
        ;
        """
        )

        self.session.commit()
        return
