# pylint: disable=redefined-outer-name
import importlib

import pytest
from graphql import graphql as execute_graphql
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from nebulous.gql.alias import Schema
from nebulous.gql.gql_database import sqla_models_to_query_object
from nebulous.sql import table_base
from nebulous.sql.reflection_utils import (
    camelize_classname,
    camelize_collection,
    pluralize_and_camelize_collection,
)
from nebulous.sql.sql_database import SQLDatabase
from nebulous.user_config import UserConfig

CONNECTION_STR = "postgresql://postgres:password@localhost:5432/pytest"


SQL_DOWN = """
    DROP SCHEMA public CASCADE;
    CREATE SCHEMA public;
    GRANT ALL ON SCHEMA public TO postgres;
"""


@pytest.fixture(scope="session")
def engine():
    _engine = create_engine(CONNECTION_STR)

    # Make sure the schema is clean
    _engine.execute(SQL_DOWN)
    yield _engine
    _engine.execute(SQL_DOWN)
    _engine.dispose()


@pytest.fixture(scope="session")
def session_maker(engine):
    smake = sessionmaker(bind=engine)
    _session = scoped_session(smake)
    yield _session


@pytest.fixture(scope="function")
def session(session_maker):
    _session = session_maker
    _session.execute(SQL_DOWN)
    _session.commit()

    yield _session

    _session.rollback()

    _session.execute(SQL_DOWN)
    _session.commit()
    _session.close()


@pytest.fixture(scope="function")
def schema_builder(session, engine):
    """Return a function that accepts a sql string
    and returns graphql schema"""
    # SQLA Metadata is preserved between tests. When we build tables in tests
    # and the tables have previously used names, the metadata is re-used and
    # differences in added/deleted columns gets janked up. Reimporting resets
    # the metadata.
    importlib.reload(table_base)
    TableBase = table_base.TableBase

    def build(sql: str):
        session.execute(sql)
        session.commit()
        TableBase.prepare(
            engine,
            reflect=True,
            schema="public",
            classname_for_table=camelize_classname,
            name_for_scalar_relationship=camelize_collection,
            name_for_collection_relationship=pluralize_and_camelize_collection,
        )

        tables = list(TableBase.classes)
        print(tables)
        query_object = sqla_models_to_query_object(tables)
        schema = Schema(query_object)
        return schema

    return build


@pytest.fixture(scope="function")
def gql_exec_builder(schema_builder, session):
    """Return a function that accepts a sql string
    and returns a graphql executor """

    def build(sql: str):
        schema = schema_builder(sql)
        return lambda request_string: execute_graphql(
            schema=schema, request_string=request_string, context={"session": session}
        )

    return build


@pytest.fixture
def sqla_db(engine):
    """An instance of SQLDatabase that is empty"""
    config = UserConfig(
        connection=None,
        schema="public",
        echo_queries=False,
        graphql_route="/graphql",
        graphiql=True,  # Not
        port=5008,
        demo=False,
    )
    # Do not delete. Used for coverage of __str__
    print(config)
    sql_db = SQLDatabase(config, engine=engine)

    yield sql_db

    # Disconnect
    sql_db.session.close()  # pylint: disable=no-member
