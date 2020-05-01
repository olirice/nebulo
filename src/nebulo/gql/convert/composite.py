# pylint: disable=invalid-name
from functools import lru_cache

from nebulo.gql.alias import Field, NonNull, ObjectType
from nebulo.text_utils import snake_to_camel
from sqlalchemy.orm import CompositeProperty


@lru_cache()
def composite_factory(sqla_composite: CompositeProperty) -> ObjectType:
    from nebulo.typemap import TypeMapper

    def build_composite_column_resolver(column_key):
        def resolver(parent, info, **kwargs):
            return parent[column_key]

        return resolver

    name = snake_to_camel(sqla_composite.key, upper=True)

    fields = {}

    for column in sqla_composite.columns:
        column_key = str(column.key)
        gql_key = snake_to_camel(column_key)
        gql_type = TypeMapper.sqla_to_gql(type(column.type))
        gql_type = NonNull(gql_type) if not column.nullable else gql_type
        gql_field = Field(gql_type, resolve=build_composite_column_resolver(column_key))
        fields[gql_key] = gql_field

    return_type = ObjectType(name, fields)
    return_type.sqla_composite = sqla_composite

    return return_type
