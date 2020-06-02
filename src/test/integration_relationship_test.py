import json

from nebulo.gql.relay.node_interface import NodeIdStructure

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


create table offer (
    id serial primary key, --integer primary key autoincrement,
    currency text,
    account_id_not_null int not null,
    account_id_nullable int,

    constraint fk_offer_account_id_not_null
        foreign key (account_id_not_null)
        references account (id),

    constraint fk_offer_account_id_nullable
        foreign key (account_id_nullable)
        references account (id)

);

INSERT INTO offer (currency, account_id_not_null, account_id_nullable) VALUES
('usd', 2, 2),
('gbp', 2, 2),
('eur', 3, null),
('jpy', 4, 4);
"""


def test_query_one_to_many(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    account_id = 2
    node_id = NodeIdStructure(table_name="account", values={"id": account_id}).serialize()
    gql_query = f"""
    {{
        account(nodeId: "{node_id}") {{
            id
            offersByIdToAccountIdNullable {{
                edges {{
                    node {{
                        id
                        currency
                    }}
                }}
            }}
        }}
    }}
    """
    result = executor(gql_query)

    print(json.dumps(result.data, indent=2))
    assert result.errors is None
    assert result.data["account"]["id"] == account_id

    offers_by_id = result.data["account"]["offersByIdToAccountIdNullable"]
    currencies = {x["node"]["currency"] for x in offers_by_id["edges"]}
    assert "usd" in currencies and "gbp" in currencies

    # Fails because sql resolver not applying join correctly
    assert len(offers_by_id["edges"]) == 2


def test_query_many_to_one(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    account_id = 2
    node_id = NodeIdStructure(table_name="account", values={"id": account_id}).serialize()
    gql_query = """
    {
      allOffers {
        edges {
            node {
                id
                accountByAccountIdNotNullToId {
                    name
                }
            }
        }
      }
    }
    """
    result = executor(gql_query)

    print(json.dumps(result.data, indent=2))
    assert result.errors is None
