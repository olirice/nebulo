SQL_UP = """
CREATE TABLE account (
    id serial primary key,
    name text not null,
    age int not null,
    created_at timestamp without time zone default (now() at time zone 'utc')
);

INSERT INTO account (id, name, age) VALUES
(1, 'oliver', 28),
(2, 'rachel', 19),
(3, 'sophie', 1),
(4, 'buddy', 19);
"""


def test_no_order(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts {{
            nodes {{
                id

            }}
       }}
    }}
    """
    result = executor(request_string=gql_query)
    assert result.errors is None


def test_order_id_asc(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts(orderBy: ID_ASC) {{
            nodes {{
                id

            }}
       }}
    }}
    """
    result = executor(request_string=gql_query)
    assert result.errors is None
    one, two, three, four = result.data["allAccounts"]["nodes"]
    assert one["id"] < two["id"] < three["id"] < four["id"]


def test_order_id_desc(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts(orderBy: ID_DESC) {{
            nodes {{
                id

            }}
       }}
    }}
    """
    result = executor(request_string=gql_query)
    assert result.errors is None
    one, two, three, four = result.data["allAccounts"]["nodes"]
    assert one["id"] > two["id"] > three["id"] > four["id"]


def test_order_multiple(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    gql_query = f"""
    {{
        allAccounts(orderBy: [AGE_ASC, NAME_DESC]) {{
            nodes {{
                id
                age
                name
            }}
       }}
    }}
    """
    result = executor(request_string=gql_query)
    assert result.errors is None
    one, two, three, four = result.data["allAccounts"]["nodes"]

    assert one["name"] == "sophie"
    assert two["name"] == "rachel"
    assert three["name"] == "buddy"
    assert four["name"] == "oliver"
