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
(4, 'buddy', 20);
"""


def test_query_with_int_condition(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts(condition: {{id: 1}}) {{
            edges {{
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    result = executor(gql_query)
    assert result.errors is None
    result_id = result.data["allAccounts"]["edges"][0]["node"]["id"]
    assert result_id == 1


def test_query_with_string_condition(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts(condition: {{name: "sophie"}}) {{
            edges {{
                node {{
                    id
                    name
                }}
            }}
        }}
    }}
    """
    result = executor(gql_query)
    assert result.errors is None
    result_name = result.data["allAccounts"]["edges"][0]["node"]["name"]
    assert result_name == "sophie"
