import pytest
from sqlalchemy import create_engine

from nebulous.sql.sql_database import SQLDatabase
from nebulous.user_config import UserConfig

from . import TEST_ROOT_DIR

CONNECTION_STR = "postgresql://postgres:password@localhost:5432/pytest"


@pytest.fixture
def engine():
    engine = create_engine(CONNECTION_STR)

    with open(TEST_ROOT_DIR / "schema_up.sql", "r") as f:
        schema_sql_str: str = f.read()

    engine.execute(schema_sql_str)
    yield engine

    with open(TEST_ROOT_DIR / "schema_down.sql", "r") as f:
        schema_sql_str: str = f.read()

    engine.dispose()


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
