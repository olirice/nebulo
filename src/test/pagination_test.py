from nebulo.gql.relay.cursor import CursorStructure

SQL_UP = """
CREATE TABLE account (
    id serial primary key,
    name text not null,
    age int not null,
    created_at timestamp without time zone default (now() at time zone 'utc')
);

INSERT INTO account (id, name, age) VALUES
(1, 'oliver', 28),
(2, 'rachel', 28),
(3, 'sophie', 1),
(4, 'buddy', 20),
(5, 'foo', 99),
(6, 'bar', 5),
(7, 'baz', 35);
"""


def test_get_cursor(client_builder):
    client = client_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200

    result = resp.json()
    assert result["errors"] == []
    cursor = result["data"]["allAccounts"]["edges"][2]["cursor"]
    assert cursor is not None


def test_invalid_cursor(client_builder):
    client = client_builder(SQL_UP)

    cursor = CursorStructure(table_name="wrong_name", values={"id": 1}).serialize()
    # Query for 1 item after the cursor
    gql_query = f"""
    {{
        allAccounts(first: 1, after: "{cursor}") {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert "invalid" in str(result["errors"][0]).lower()


def test_retrieve_1_after_cursor(client_builder):
    client = client_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []
    # Get a cursor to 2nd entry
    cursor = result["data"]["allAccounts"]["edges"][1]["cursor"]

    # Query for 1 item after the cursor
    gql_query = f"""
    {{
        allAccounts(first: 1, after: "{cursor}") {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []

    assert result["data"]["allAccounts"]["edges"][0]["node"]["id"] == 3


def test_retrieve_1_before_cursor(client_builder):
    client = client_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []

    # Get a cursor to 2nd entry
    cursor = result["data"]["allAccounts"]["edges"][1]["cursor"]
    print(cursor)

    # Query for 1 item after the cursor
    gql_query = f"""
    {{
        allAccounts(last: 1, before: "{cursor}") {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []

    assert result["data"]["allAccounts"]["edges"][0]["node"]["id"] == 1


def test_first_without_after(client_builder):
    client = client_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []

    # Get a cursor to 2nd entry
    cursor = result["data"]["allAccounts"]["edges"][1]["cursor"]
    print(cursor)

    # Query for 1 item after the cursor
    gql_query = f"""
    {{
        allAccounts(first: 1) {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []

    assert result["data"]["allAccounts"]["edges"][0]["node"]["id"] == 1


def test_last_without_before(client_builder):
    client = client_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []

    # Get a cursor to 2nd entry
    cursor = result["data"]["allAccounts"]["edges"][1]["cursor"]
    print(cursor)

    # Query for 1 item after the cursor
    gql_query = f"""
    {{
        allAccounts(last: 1) {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []

    assert result["data"]["allAccounts"]["edges"][0]["node"]["id"] == 7


def test_pagination_order(client_builder):
    client = client_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []

    # Get a cursor to 2nd entry
    # Cursor for the "rachel" entry
    limit = 2
    after_cursor = result["data"]["allAccounts"]["edges"][1]["cursor"]
    # Cursor for the "buddy" entry, id = 4
    before_cursor = result["data"]["allAccounts"]["edges"][3]["cursor"]

    # Query for 2 rows after the cursor
    gql_query = f"""
    {{
        allAccounts(first: {limit}, after: "{after_cursor}") {{
            edges {{
                cursor
                node {{
                    id
                    name
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []

    after_result = [x["node"]["name"] for x in result["data"]["allAccounts"]["edges"]]
    assert after_result == ["sophie", "buddy"]

    gql_query = f"""
    {{
        allAccounts(last: {limit}, before: "{before_cursor}") {{
            edges {{
                cursor
                node {{
                    id
                    name
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []

    assert [x["node"]["name"] for x in result["data"]["allAccounts"]["edges"]] == ["rachel", "sophie"]


def test_invalid_pagination_params(client_builder):
    client = client_builder(SQL_UP)
    cursor = CursorStructure(table_name="not used", values={"id": 1}).serialize()
    # First with Before
    gql_query = f"""
    {{
        allAccounts(first: 1, before: "{cursor}") {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] != []

    # Last with After
    gql_query = f"""
    {{
        allAccounts(last: 1, after: "{cursor}") {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] != []

    # First and Last
    gql_query = f"""
    {{
        allAccounts(first: 1, last: 1) {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] != []

    # Before and After
    gql_query = f"""
    {{
        allAccounts(before: "{cursor}", after: "{cursor}") {{
            edges {{
                cursor
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    with client:
        resp = client.post("/", json={"query": gql_query})
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] != []
