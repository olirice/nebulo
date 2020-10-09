import json

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
(3, 'sophie');
"""


def test_delete_mutation(client_builder):
    client = client_builder(SQL_UP)
    account_id = 1
    node_id = NodeIdStructure(table_name="account", values={"id": account_id}).serialize()
    query = f"""

mutation {{
  deleteAccount(input: {{
    clientMutationId: "gjwl"
    nodeId: "{node_id}"
  }}) {{
    cid: clientMutationId
    nodeId
  }}
}}
    """

    with client:
        resp = client.post("/", json={"query": query})
    assert resp.status_code == 200
    payload = json.loads(resp.text)
    print(payload)
    assert isinstance(payload["data"]["deleteAccount"], dict)
    assert payload["data"]["deleteAccount"]["cid"] == "gjwl"
    assert payload["data"]["deleteAccount"]["nodeId"] == node_id
    assert len(payload["errors"]) == 0
