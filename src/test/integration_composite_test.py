from nebulo.gql.convert.node_interface import to_global_id

SQL_UP = """
create type human_name as (
      first text,
      last text 
);

CREATE TABLE account (
    id serial primary key,
    name human_name not null
);

INSERT INTO account (id, name) VALUES
(1, ('oliver', 'rice')::human_name);
"""


def test_query_multiple_fields(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    account_id = 1
    node_id = to_global_id(table_name="account", values=[account_id])
    gql_query = f"""
    {{
        account(nodeId: "{node_id}") {{
            id
            name {{
                first
            }}
        }}
    }}
    """
    result = executor(gql_query)
    assert result.errors is None
    assert result.data["account"]["id"] == account_id
    assert result.data["account"]["name"] == "oliver"
    assert isinstance(result.data["account"]["createdAt"], str)
