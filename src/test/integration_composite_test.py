from nebulo.gql.relay.node_interface import NodeIdStructure

SQL_UP = """
CREATE TYPE full_name AS (
    first_name       text,
    last_name        text
);

create table account (
    id serial primary key,
    name full_name not null
);

insert into account(name) values
(('oliver', 'rice'));
"""


def test_query_multiple_fields(client_builder):
    client = client_builder(SQL_UP)
    account_id = 1
    node_id = NodeIdStructure(table_name="account", values={"id": account_id}).serialize()
    gql_query = f"""
    {{
        account(nodeId: "{node_id}") {{
            id
            name {{
                first_name
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200

    result = resp.json()

    assert result["errors"] == []
    assert result["data"]["account"]["id"] == account_id
    assert result["data"]["account"]["name"]["first_name"] == "oliver"
