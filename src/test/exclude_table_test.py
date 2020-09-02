SQL_SETUP = """
create table friend(
    id serial primary key,
    email text,
    dob date,
    created_at timestamp
);

comment on table friend is E'@exclude read';
"""


def test_exclude_table(schema_builder):
    schema = schema_builder(SQL_SETUP)
    assert schema.query_type is None
    assert schema.mutation_type is not None
