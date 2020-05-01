from nebulo.sql.reflection.function import reflect_functions

CREATE_FUNCTION = """
create function public.to_upper(some_text text)
returns text
as $$
    select upper(some_text);
$$ language sql;
"""


def test_reflect_function(engine, session):
    session.execute(CREATE_FUNCTION)
    session.commit()

    functions = reflect_functions(engine, schema="public")

    to_upper = [x for x in functions if x.name == "to_upper"]
    assert len(to_upper) == 1


def test_call_function(engine, session):
    session.execute(CREATE_FUNCTION)
    session.commit()

    functions = reflect_functions(engine, schema="public")
    to_upper = [x for x in functions if x.name == "to_upper"][0]

    result = to_upper.call(session, {"some_text": "abc"})
    assert result == "ABC"
