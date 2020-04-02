import json

from nebulo.gql.convert.node_interface import to_global_id

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
    account_id int not null,

    constraint fk_offer_account_id
        foreign key (account_id)
        references account (id)
);

INSERT INTO offer (currency, account_id) VALUES
('usd', 2),
('gbp', 2),
('eur', 3),
('jpy', 4);
"""


def test_query_one_to_many(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    account_id = 2
    node_id = to_global_id(table_name="account", values=[account_id])
    gql_query = f"""
    {{
        account(nodeId: "{node_id}") {{
            id
            offersByAccountId {{
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

    offers_by_id = result.data["account"]["offersByAccountId"]
    currencies = {x["node"]["currency"] for x in offers_by_id["edges"]}
    assert "usd" in currencies and "gbp" in currencies

    # Fails because sql resolver not applying join correctly
    assert len(offers_by_id["edges"]) == 2


def test_query_many_to_one(gql_exec_builder):
    executor = gql_exec_builder(SQL_UP)
    account_id = 2
    node_id = to_global_id(table_name="account", values=[account_id])
    gql_query = """
    {
      allOffers {
        edges {
            node {
                id
                accountByAccountId {
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
