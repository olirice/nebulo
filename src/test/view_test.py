SQL_UP = """
create table account (
    id serial primary key,
    name text not null
);

create view account_view as
select
    id account_id,
    name account_name
from
    account;


comment on view account_view IS E'
@foreign_key (account_id) references public.account (id)
@primary_key (account_id)';


insert into account(id, name) values
(1, 'Oliver');
"""


def test_reflect_view(schema_builder):
    schema = schema_builder(SQL_UP)

    query_type = schema.query_type
    assert "accountView" in query_type.fields

    mutation_type = schema.mutation_type
    assert "createAccountView" not in mutation_type.fields
    assert "updateAccountView" not in mutation_type.fields
    assert "deleteAccountView" not in mutation_type.fields


def test_query_view(client_builder):
    client = client_builder(SQL_UP)

    gql_query = """
    query {
      allAccountViews {
        edges {
          node {
            nodeId
            accountId
            accountName
            accountByAccountIdToId{
              name
            }
          }
        }
      }
    }
    """

    with client:
        resp = client.post("/", json={"query": gql_query})
    result = resp.json()
    assert resp.status_code == 200

    print(result)
    assert result["errors"] == []
    assert result["data"]["allAccountViews"]["edges"][0]["node"]["accountId"] == 1
    assert result["data"]["allAccountViews"]["edges"][0]["node"]["accountByAccountIdToId"]["name"] == "Oliver"
