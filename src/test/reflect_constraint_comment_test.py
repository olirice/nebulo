from nebulo.sql.inspect import get_comment, get_constraints, get_table_name
from nebulo.sql.reflection.manager import reflect_sqla_models

SQL_UP = """
CREATE TABLE public.person (
    id serial primary key
);

CREATE TABLE public.address (
    id serial primary key,
    person_id int,

    constraint fk_person foreign key (person_id) references public.person (id)
);

comment on constraint fk_person on public.address is '@name Person Addresses';
"""


def test_reflect_fkey_comment(engine):
    engine.execute(SQL_UP)
    tables, _ = reflect_sqla_models(engine, schema="public")

    table = [x for x in tables if get_table_name(x) == "address"][0]

    constraint = [x for x in get_constraints(table) if x.name == "fk_person"][0]
    assert get_comment(constraint) == "@name Person Addresses"


def test_reflect_fkey_comment_to_schema(schema_builder):
    schema = schema_builder(SQL_UP)
    assert "Addresses" in schema.type_map["Person"].fields
    assert "Person" in schema.type_map["Address"].fields
