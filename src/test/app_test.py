from __future__ import annotations

import json
import typing

if typing.TYPE_CHECKING:
    from starlette.applications import Starlette

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


CREATE FUNCTION to_lower(some_text text) returns text as
$$ select lower(some_text) $$ language sql immutable;
"""


def test_app_has_route(app_builder):
    app: Starlette = app_builder(SQL_UP)
    routes: typing.List[str] = [x.path for x in app.routes]
    assert "/" in routes


def test_app_serves_graphiql(client_builder):
    client = client_builder(SQL_UP)
    headers = {"Accept": "text/html"}
    with client:
        resp = client.get("/graphiql", headers=headers)
    print(resp)
    assert resp.status_code == 200


def test_app_serves_graphql_query_from_application_json(client_builder):
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

    with client:
        resp = client.post("/", json={"query": query})
    assert resp.status_code == 200
    print(resp.text)

    payload = json.loads(resp.text)
    assert "data" in payload
    assert len(payload["data"]["allAccounts"]["edges"]) == 4


def test_app_serves_mutation_function(client_builder):
    client = client_builder(SQL_UP)

    query = """
    query {
        toLower(some_text: "AbC")
    }
    """

    with client:
        resp = client.post("/", json={"query": query})
    assert resp.status_code == 200
    print(resp.text)

    payload = json.loads(resp.text)
    assert "data" in payload
    assert payload["data"]["toLower"] == "abc"
