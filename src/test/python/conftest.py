import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from nebulous.sql.sql_database import SQLDatabase
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
    sql_db = SQLDatabase(config, engine=engine)

    yield sql_db

    # Disconnect
    sql_db.session.close()  # pylint: disable=no-member
