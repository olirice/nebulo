from nebulous.gql.convert.node_interface import to_global_id

SQL_UP = """
CREATE TABLE account (
    id serial primary key
);

INSERT INTO account (id) VALUES
(1),
(2),
(3);
"""


def test_query_node_id(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)

    account_id = 1
    node_id = to_global_id(name="account", _id=account_id)

    gql_query = f"""
    {{
        account(NodeID: "{node_id}") {{
            nodeId
        }}
    }}
    """
    result = executor(gql_query)
    print(result.data)
    assert result.errors is None
    assert result.data["account"]["nodeId"] == node_id

    wrong_node_id = to_global_id(name="account", _id=2)
    assert result.data["account"]["nodeId"] != wrong_node_id
