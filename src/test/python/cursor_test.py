from nebulo.gql.convert.cursor import to_cursor

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


def test_get_cursor(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
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
    result = executor(request_string=gql_query)
    assert result.errors is None
    cursor = result.data["allAccounts"]["edges"][2]["cursor"]
    assert cursor is not None


def test_invalid_cursor(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)

    cursor = to_cursor("wrong_name", [1])
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
    result = executor(request_string=gql_query)
    assert "invalid" in result.errors[0].message.lower()


def test_retrieve_1_after_cursor(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
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
    result = executor(request_string=gql_query)
    # Get a cursor to 2nd entry
    cursor = result.data["allAccounts"]["edges"][1]["cursor"]
    print(cursor)

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
    result = executor(request_string=gql_query)
    assert result.data["allAccounts"]["edges"][0]["node"]["id"] == 3
