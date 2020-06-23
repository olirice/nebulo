SQL_SETUP = """
create table person(
    id serial primary key,
    email text,
    dob date,
    created_at timestamp
);

comment on column person.created_at is E'@exclude insert, update';
comment on column person.email is E'@exclude update';
comment on column person.dob is E'@exclude read';
"""


def test_reflect_function(schema_builder):
    schema = schema_builder(SQL_SETUP)

    assert "id" in schema.type_map["Person"].fields
    assert "dob" not in schema.type_map["Person"].fields
    assert "createdAt" in schema.type_map["Person"].fields
    assert "createdAt" not in schema.type_map["PersonInput"].fields
    assert "createdAt" not in schema.type_map["PersonPatch"].fields
    assert "email" in schema.type_map["PersonInput"].fields
    assert "email" not in schema.type_map["PersonPatch"].fields
