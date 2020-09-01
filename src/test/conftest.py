# pylint: disable=redefined-outer-name
from __future__ import annotations

import asyncio
import importlib
from typing import Callable, Optional

import pytest
from graphql import graphql_sync as execute_graphql
from graphql.execution.execute import ExecutionResult
from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
from nebulo.server.starlette import create_app
from nebulo.sql import table_base
from nebulo.sql.reflection.manager import reflect_sqla_models
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from starlette.applications import Starlette
from starlette.testclient import TestClient

SQL_DOWN = """
    DROP SCHEMA public CASCADE;
    CREATE SCHEMA public;
    GRANT ALL ON SCHEMA public TO nebulo_user;
"""


@pytest.fixture(scope="session")
def event_loop():
    """ Event loop for use testing async functions """
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def connection_str():
    """ SQLAlchemy connection string to test database """
    return "postgresql://nebulo_user:password@localhost:4442/nebulo_db"


@pytest.fixture(scope="session")
def engine(connection_str: str):
    """ SQLAlchemy engine """
    _engine = create_engine(connection_str, echo=False)
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


@pytest.fixture
def reset_sqla() -> None:
    """SQLA Metadata is preserved between tests. When we build tables in tests
    and the tables have previously used names, the metadata is re-used and
    differences in added/deleted columns gets janked up. Reimporting resets
    the metadata."""
    importlib.reload(table_base)


@pytest.fixture
def session(session_maker, reset_sqla):  # pylint: disable=unused-argument
    _session = session_maker
    _session.execute(SQL_DOWN)
    _session.commit()
    yield _session
    _session.rollback()
    _session.execute(SQL_DOWN)
    _session.commit()
    _session.close()


@pytest.fixture
def schema_builder(session, engine):
    """Return a function that accepts a sql string
    and returns graphql schema"""

    def build(sql: str):
        session.execute(sql)
        session.commit()
        TableBase = table_base.TableBase  # pylint: disable=invalid-name
        tables, functions = reflect_sqla_models(engine, schema="public", declarative_base=TableBase)
        schema = sqla_models_to_graphql_schema(tables, functions, resolve_async=False)
        return schema

    yield build


@pytest.fixture
def gql_exec_builder(schema_builder, session) -> Callable[[str], Callable[[str], ExecutionResult]]:
    """Return a function that accepts a sql string
    and returns a graphql executor"""

    def build(sql: str) -> Callable[[str], ExecutionResult]:
        schema = schema_builder(sql)
        return lambda source_query: execute_graphql(
            schema=schema, source=source_query, context_value={"session": session, "jwt_claims": {}}
        )

    return build


@pytest.fixture
def app_builder(event_loop, connection_str, session) -> Callable[[str, Optional[str], Optional[str]], Starlette]:
    def build(sql: str, jwt_identifier: Optional[str] = None, jwt_secret: Optional[str] = None) -> Starlette:
        session.execute(sql)
        session.commit()

        # Create the schema
        app = create_app(connection_str, jwt_identifier=jwt_identifier, jwt_secret=jwt_secret)
        return app

    return build


@pytest.fixture
def client_builder(
    app_builder: Callable[[str, Optional[str], Optional[str]], Starlette]
) -> Callable[[str, Optional[str], Optional[str]], TestClient]:
    # NOTE: Client must be used as a context manager for on_startup and on_shutdown to execute
    # e.g. connect to the database

    def build(sql: str, jwt_identifier: Optional[str] = None, jwt_secret: Optional[str] = None) -> TestClient:
        importlib.reload(table_base)
        app = app_builder(sql, jwt_identifier, jwt_secret)
        client = TestClient(app)
        return client

    return build
