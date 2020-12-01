SQL_UP = """
CREATE TABLE public.person (
    id serial primary key
);

CREATE TABLE public.address (
    id serial primary key,
    person_id int,

    constraint fk_person foreign key (person_id) references public.person (id)
);

comment on constraint fk_person on public.address is '@name Person Addresses
@exclude read
';
"""


def test_fkey_comment_exclude_one(schema_builder):
    schema = schema_builder(SQL_UP)
    assert "Addresses" not in schema.type_map["Person"].fields
    assert "Person" not in schema.type_map["Address"].fields
