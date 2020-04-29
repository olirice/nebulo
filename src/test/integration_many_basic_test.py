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


def test_query_multiple_fields(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    gql_query = f"""
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
    result = executor(gql_query)
    assert result.errors is None
    assert "edges" in result.data["allAccounts"]
    assert "node" in result.data["allAccounts"]["edges"][0]


def test_arg_first(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts(first: 2) {{
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
    result = executor(gql_query)
    assert result.errors is None
    assert len(result.data["allAccounts"]["edges"]) == 2
    assert result.data["allAccounts"]["edges"][0]["node"]["id"] == 1
    assert result.data["allAccounts"]["edges"][1]["node"]["id"] == 2
