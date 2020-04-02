# pylint: disable=redefined-outer-name
import pytest
from graphql import graphql as execute_graphql
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from nebulous.gql.alias import Schema
from nebulous.gql.gql_database import sqla_models_to_query_object
from nebulous.sql.sql_database import SQLDatabase
from nebulous.sql.table_base import TableBase
from nebulous.user_config import UserConfig

from . import TEST_ROOT_DIR

CONNECTION_STR = "postgresql://postgres:password@localhost:5432/pytest"


with open(TEST_ROOT_DIR / "schema_down.sql", "r") as f:
    SQL_DOWN = f.read()


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
    yield smake


@pytest.fixture(scope="function")
def session(session_maker):
    _session = scoped_session(session_maker)
    yield _session
    _session.execute(SQL_DOWN)
    _session.commit()
    _session.close()


@pytest.fixture(scope="function")
def schema_builder(engine):
    """Return a function that accepts a sql string
    and returns graphql schema"""

    def build(sql: str):
        engine.execute(sql)
        TableBase.prepare(engine, reflect=True, schema="public")
        tables = list(TableBase.classes)
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
    print(config)
    sql_db = SQLDatabase(config, engine=engine)

    yield sql_db

    # Disconnect
    sql_db.session.close()  # pylint: disable=no-member
