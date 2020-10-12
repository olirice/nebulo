from nebulo.gql.relay.node_interface import NodeIdStructure

SQL_UP = """
CREATE TABLE account (
    id serial primary key
);

INSERT INTO account (id) VALUES
(1),
(2),
(3);
"""


def test_round_trip_node_id(client_builder):
    client = client_builder(SQL_UP)

    account_id = 1
    node_id = NodeIdStructure(table_name="account", values={"id": account_id}).serialize()

    gql_query = f"""
    {{
        account(nodeId: "{node_id}") {{
            nodeId
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200

    result = resp.json()
    assert result["errors"] == []

    assert result["data"]["account"]["nodeId"] == node_id

    wrong_node_id = NodeIdStructure(table_name="account", values={"id": 2}).serialize()
    assert result["data"]["account"]["nodeId"] != wrong_node_id


def test_invalid_node_id(client_builder):
    client = client_builder(SQL_UP)

    invalid_node_id = "not_a_valid_id"

    gql_query = f"""
    {{
        account(nodeId: "{invalid_node_id}") {{
            nodeId
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200

    result = resp.json()
    assert len(result["errors"]) == 1
    assert "Expected value of type" in str(result["errors"][0])
