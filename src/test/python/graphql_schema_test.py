from .conftests import engine, session, session_maker
from nebulous.sql.table_base import TableBase
from nebulous.gql.gql_database import sqla_models_to_query_object
from nebulous.gql.alias import Schema
from graphql import graphql
from nebulous.gql.convert.node_interface import to_global_id

import sqlalchemy as sqla

__all__ = ['engine', 'session', 'session_maker']


SQL_UP = """
CREATE TABLE account (
    id serial primary key, --integer primary key autoincrement,
    name text not null,
    created_at timestamp without time zone default (now() at time zone 'utc')
);

INSERT INTO account (id, name) VALUES
(1, 'oliver'),
(2, 'rachel'),
(3, 'sophie'),
(4, 'buddy');
"""


def test_query_one(engine, session):
    engine.execute(SQL_UP)
    TableBase.prepare(engine, reflect=True, schema="public")

    account = TableBase.classes["account"]
    query_object = sqla_models_to_query_object([account])
    schema = Schema(query_object)

    account_id = 1

    node_id = to_global_id(name="account", _id=account_id)
    gql_query = f"""
    {{
        account(NodeID: "{node_id}") {{
            id
        }}
    }}
    """
    result = graphql(schema, gql_query, context_value={"session": session})
    print(result.data)
    assert result.errors is None
    assert result.data['account']['id'] == account_id


