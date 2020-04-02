from graphql.error.located_error import GraphQLLocatedError

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
            nodes {{
                id
                name
                created_at
            }}
        }}
    }}
    """
    result = executor(request_string=gql_query)
    assert result.errors is None
    assert "nodes" in result.data["allAccounts"]


def test_arg_first(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts(first: 2) {{
            nodes {{
                id
            }}
        }}
    }}
    """
    result = executor(request_string=gql_query)
    assert result.errors is None
    assert len(result.data["allAccounts"]["nodes"]) == 2
    assert result.data["allAccounts"]["nodes"][0]["id"] == 1
    assert result.data["allAccounts"]["nodes"][1]["id"] == 2


def test_arg_last_requires_before_cursor(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts(last: 2) {{
            nodes {{
                id
            }}
        }}
    }}
    """
    result = executor(request_string=gql_query)
    assert len(result.errors) == 1
    error: GraphQLLocatedError = result.errors[0]
    assert "cursor is required" in error.message
