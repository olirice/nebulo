from __future__ import annotations

from cachetools import cached
from nebulo.gql.alias import ObjectType, Schema
from nebulo.gql.entrypoints.many import many_node_factory
from nebulo.gql.entrypoints.one import one_node_factory
from nebulo.sql.inspect import get_table_name
from nebulo.text_utils import snake_to_camel, to_plural


@cached(cache={}, key=tuple)
def sqla_models_to_graphql_schema(sqla_models) -> Schema:
    """Creates a GraphQL Schema from SQLA Models"""

    query_fields = {
        **{f"{snake_to_camel(get_table_name(x), upper=False)}": one_node_factory(x) for x in sqla_models},
        **{f"all{snake_to_camel(to_plural(get_table_name(x)))}": many_node_factory(x) for x in sqla_models},
    }

    query_object = ObjectType(name="Query", fields=lambda: query_fields)
    return Schema(query_object)
