from nebulo.gql.relay.node_interface import NodeIdStructure

SQL_UP = """
create table book(
    id serial primary key,
    flags bool[]
);

insert into book(flags) values
('{true,false}'::bool[]);
"""


def test_query_multiple_fields(client_builder):
    client = client_builder(SQL_UP)
    book_id = 1
    node_id = NodeIdStructure(table_name="book", values={"id": book_id}).serialize()
    gql_query = f"""
    {{
        book(nodeId: "{node_id}") {{
            id
            flags
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200

    result = resp.json()

    assert result["errors"] == []
    assert result["data"]["book"]["id"] == book_id
    assert result["data"]["book"]["flags"] == [True, False]
