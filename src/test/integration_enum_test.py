from nebulo.gql.relay.node_interface import NodeIdStructure

SQL_UP = """
CREATE TYPE light_color AS ENUM ('red', 'green', 'blue');

create table light(
    id serial primary key,
    color light_color
);

insert into light(color) values
('green');
"""


def test_query_multiple_fields(client_builder):
    client = client_builder(SQL_UP)
    light_id = 1
    node_id = NodeIdStructure(table_name="light", values={"id": light_id}).serialize()
    gql_query = f"""
    {{
        light(nodeId: "{node_id}") {{
            id
            color
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200

    result = resp.json()

    assert result["errors"] == []
    assert result["data"]["light"]["id"] == light_id
    assert result["data"]["light"]["color"] == "green"
