from __future__ import annotations

import json

import pytest

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


@pytest.mark.skip(reason="need app fixture")
def test_app_has_route(app_builder):
    app = app_builder(SQL_UP)
    routes = {x.endpoint for x in app.url_map.iter_rules()}
    assert "graphql" in routes


@pytest.mark.skip(reason="need app fixture")
def test_app_serves_graphiql(client_builder):
    client = client_builder(SQL_UP)
    headers = {"Accept": "text/html"}
    resp = client.get("/graphql", headers=headers)
    assert resp.status == "200 OK"


@pytest.mark.skip(reason="need app fixture")
def test_app_serves_graphql_query(client_builder):
    client = client_builder(SQL_UP)

    query = f"""
    {{
        allAccounts {{
            edges {{
                node {{
                    id
                    name
                    createdAt
                }}
            }}
        }}
    }}
    """
    resp = client.post("/graphql", json={"query": query})
    assert resp.status == "200 OK"
    payload = json.loads(resp.data)
    assert "data" in payload
    assert len(payload["data"]["allAccounts"]["edges"]) == 4
