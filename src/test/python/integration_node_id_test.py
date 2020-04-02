from graphql import graphql

from nebulous.gql.alias import Schema
from nebulous.gql.convert.node_interface import to_global_id
from nebulous.gql.gql_database import sqla_models_to_query_object
from nebulous.sql.table_base import TableBase

SQL_UP = """
CREATE TABLE account (
    id serial primary key
);

INSERT INTO account (id) VALUES
(1),
(2),
(3);
"""


def test_query_node_id(engine, session):
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
            nodeId
        }}
    }}
    """
    result = graphql(schema, gql_query, context={"session": session})
    print(result.data)
    assert result.errors is None
    assert result.data["account"]["nodeId"] == node_id

    wrong_node_id = to_global_id(name="account", _id=2)
    assert result.data["account"]["nodeId"] != wrong_node_id
