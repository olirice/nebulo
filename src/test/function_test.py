from nebulo.sql.reflection.function import reflect_functions
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

    query = to_upper.to_executable({"some_text": "abc"})
    result = session.execute(query).fetchone()["to_upper"]
    assert result == "ABC"


def test_integration_function(gql_exec_builder):
    executor = gql_exec_builder(CREATE_FUNCTION)

    gql_query = """
    mutation {
        toUpper(some_text: "abc")
    }
    """

    result = executor(gql_query)
    assert result.errors is None
    assert result.data["toUpper"] == "ABC"
