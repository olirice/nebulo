from graphql import graphql

from nebulous.gql.alias import Schema
from nebulous.gql.convert.node_interface import to_global_id
from nebulous.gql.gql_database import sqla_models_to_query_object
from nebulous.sql.table_base import TableBase

SQL_UP = """
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
"""


def test_query_one_field(engine, session):
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
    result = graphql(schema, gql_query, context={"session": session})
    print(result.data)
    assert result.errors is None
    assert isinstance(result.data["account"], dict)
    assert result.data["account"]["id"] == account_id


def test_query_multiple_fields(engine, session):
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
            name
            created_at
        }}
    }}
    """
    result = graphql(schema, gql_query, context={"session": session})
    assert result.errors is None
    assert result.data["account"]["id"] == account_id
    assert result.data["account"]["name"] == "oliver"
    assert isinstance(result.data["account"]["created_at"], str)
