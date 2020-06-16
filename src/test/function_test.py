import json

from nebulo.sql.reflection.function import reflect_functions
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import base as pg_base

CREATE_FUNCTION = """
create function public.to_upper(some_text text)
returns text
as $$
    select upper(some_text);
$$ language sql;


-- solve query root type nust not be none issue
create table trash (
    id serial primary key
);
"""


def test_reflect_function(engine, session):
    session.execute(CREATE_FUNCTION)
    session.commit()

    functions = reflect_functions(engine, schema="public", type_map=pg_base.ischema_names)

    to_upper = [x for x in functions if x.name == "to_upper"]
    assert len(to_upper) == 1


def test_call_function(engine, session):
    session.execute(CREATE_FUNCTION)
    session.commit()

    functions = reflect_functions(engine, schema="public", type_map=pg_base.ischema_names)
    to_upper = [x for x in functions if x.name == "to_upper"][0]

    query = select([to_upper.to_executable(["abc"]).label("result")])
    result = session.execute(query).fetchone()["result"]
    assert result == "ABC"


def test_integration_function(client_builder):
    client = client_builder(CREATE_FUNCTION)

    query = """
    mutation {
        toUpper(input: {some_text: "abc", clientMutationId: "some_client_id"}) {
            result
            clientMutationId
        }
    }
    """

    with client:
        resp = client.post("/", json={"query": query})
    result = json.loads(resp.text)
    assert resp.status_code == 200
    assert result["errors"] == []
    assert result["data"]["toUpper"]["result"] == "ABC"
