from nebulous.gql.convert.node_interface import to_global_id

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


def skip_temporary():
    def test_query_one_to_many(gql_exec_builder):
        executor = gql_exec_builder(SQL_UP)
        account_id = 2
        node_id = to_global_id(name="account", _id=account_id)
        gql_query = f"""
        {{
            account(nodeId: "{node_id}") {{
                id
                offersById {{
                    nodes {{
                        id
                        currency
                    }}
                }}
            }}
        }}
        """
        result = executor(gql_query)
        import json

        print(json.dumps(result.data, indent=2))
        assert result.errors is None
        assert result.data["account"]["id"] == account_id

        offers_by_id = result.data["account"]["offersById"]
        currencies = {x["currency"] for x in offers_by_id["nodes"]}
        assert "usd" in currencies and "gbp" in currencies

        # Fails because sql resolver not applying join correctly
        assert len(offers_by_id["nodes"]) == 2
