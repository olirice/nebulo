# pylint: disable=redefined-outer-name
from __future__ import annotations

import importlib
from typing import Callable

import pytest
from graphql import graphql_sync as execute_graphql
from graphql.execution.execute import ExecutionResult
from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
from nebulo.sql import table_base
from nebulo.sql.reflection_utils import (
    rename_columns,
    rename_table,
    rename_to_many_collection,
    rename_to_one_collection,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

SQL_DOWN = """
    DROP SCHEMA public CASCADE;
    CREATE SCHEMA public;
    GRANT ALL ON SCHEMA public TO nebulo_user;
"""


@pytest.fixture(scope="session")
def connection_str():
    return "postgresql://nebulo_user:password@localhost:4442/nebulo_db"


@pytest.fixture(scope="session")
def engine(connection_str):
    _engine = create_engine(connection_str)
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
def session(session_maker):
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
    # SQLA Metadata is preserved between tests. When we build tables in tests
    # and the tables have previously used names, the metadata is re-used and
    # differences in added/deleted columns gets janked up. Reimporting resets
    # the metadata.
    importlib.reload(table_base)
    TableBase = table_base.TableBase  # pylint: disable=invalid-name

    def build(sql: str):
        session.execute(sql)
        session.commit()
        rename_columns()
        TableBase.prepare(
            engine,
            reflect=True,
            schema="public",
            classname_for_table=rename_table,
            name_for_scalar_relationship=rename_to_one_collection,
            name_for_collection_relationship=rename_to_many_collection,
        )
        tables = list(TableBase.classes)
        schema = sqla_models_to_graphql_schema(tables, resolve_async=False)
        return schema

    return build


@pytest.fixture
def gql_exec_builder(schema_builder, session) -> Callable[[str], Callable[[str], ExecutionResult]]:
    """Return a function that accepts a sql string
    and returns a graphql executor """

    def build(sql: str) -> Callable[[str], ExecutionResult]:
        schema = schema_builder(sql)
        return lambda source_query: execute_graphql(
            schema=schema, source=source_query, context_value={"session": session}
        )

    return build
