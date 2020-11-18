SQL_SETUP = """
create table person(
    id serial primary key,
    email text,
    dob date,
    created_at timestamp
);

comment on column person.email is E'@name contact_email';
"""


def test_reflect_column_name_directive(schema_builder):
    schema = schema_builder(SQL_SETUP)

    assert "email" not in schema.type_map["Person"].fields
    assert "contact_email" in schema.type_map["Person"].fields
