from nebulo.gql.relay.node_interface import NodeIdStructure

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


def test_query_one_field(client_builder):
    client = client_builder(SQL_UP)
    account_id = 1
    node_id = NodeIdStructure(table_name="account", values={"id": account_id}).serialize()
    gql_query = f"""
    {{
        account(nodeId: "{node_id}") {{
            id
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200

    result = resp.json()
    assert isinstance(result["data"]["account"], dict)
    assert result["data"]["account"]["id"] == account_id


def test_query_multiple_fields(client_builder):
    client = client_builder(SQL_UP)
    account_id = 1
    node_id = NodeIdStructure(table_name="account", values={"id": account_id}).serialize()
    gql_query = f"""
    {{
        account(nodeId: "{node_id}") {{
            id
            name
            createdAt
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200

    result = resp.json()

    assert result["errors"] == []
    assert result["data"]["account"]["id"] == account_id
    assert result["data"]["account"]["name"] == "oliver"
    assert isinstance(result["data"]["account"]["createdAt"], str)
