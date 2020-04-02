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

def test_query_multiple_fields(gql_exec_builder, benchmark):
    executor = gql_exec_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccount {{
            nodes {{
                id
                name
                created_at
            }}
        }}
    }}
    """
    result = benchmark(executor, request_string=gql_query)
    assert result.errors is None
    assert "nodes" in result.data["allAccount"]
