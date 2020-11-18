SQL_SETUP = """
create table friend(
    id serial primary key,
    email text,
    dob date,
    created_at timestamp
);

comment on table friend is E'@name Associate';
"""


def test_reflect_table_name_directive(schema_builder):
    schema = schema_builder(SQL_SETUP)

    assert "Friend" not in schema.type_map
    assert "friend" not in schema.type_map
    assert "Associate" in schema.type_map
