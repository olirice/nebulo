import json

from nebulo.sql.reflection.function import reflect_functions
from sqlalchemy.dialects.postgresql import base as pg_base

CREATE_FUNCTION = """
create table account(
    id int primary key
);

insert into account (id)
values (1);

create function get_account(id int)
returns account
as $$
    select 1;
$$ language sql;
"""


def test_reflect_function_returning_row(engine, session):
    session.execute(CREATE_FUNCTION)
    session.commit()

    functions = reflect_functions(engine, schema="public", type_map=pg_base.ischema_names)

    get_account = functions[0]
    res = session.execute(get_account.to_executable([1])).first()
    print(res)
    # psycopg2 does not know how to deserialize row results
    assert res == ("(1)",)


def test_integration_function(client_builder):
    client = client_builder(CREATE_FUNCTION)

    query = """
    mutation {
        getAccount(input: {id: 1, clientMutationId: "abcdef"}) {
            cmi: clientMutationId
            out: result {
                nodeId
                id
            }
        }
    }
    """

    with client:
        resp = client.post("/", json={"query": query})
    result = json.loads(resp.text)
    print(result)
    assert resp.status_code == 200
    assert result["errors"] == []
    assert result["data"]["getAccount"]["out"]["id"] == 1
    assert result["data"]["getAccount"]["out"]["nodeId"] is not None
    assert result["data"]["getAccount"]["cmi"] == "abcdef"
