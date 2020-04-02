from __future__ import annotations

from typing import TYPE_CHECKING

from nebulo.gql.alias import ObjectType, Schema
from nebulo.gql.entrypoints.many import many_node_factory
from nebulo.gql.entrypoints.one import one_node_factory
from nebulo.sql.inspect import get_table_name
from nebulo.text_utils import snake_to_camel, to_plural

if TYPE_CHECKING:
    from nebulo.sql.sql_database import SQLDatabase


class GQLDatabase:
    def __init__(self, sqldb: SQLDatabase):
        # GQL Tables
        self.sqldb = sqldb

        # self.gql_models: List[GraphQLObjectType] = [convert_table(x) for x in sqldb.models]
        # self.gql_functions: List[ReflectedGQLFunction] = [
        #    function_reflection_factory(x) for x in sqldb.functions
        # ]

        # GQL Schema
        self.schema = Schema(sqla_models_to_query_object(sqldb.models))


def sqla_models_to_query_object(sqla_models):
    """Creates a base query object from available graphql objects/tables"""
    query_fields = {
        **{f"{snake_to_camel(get_table_name(x), upper=False)}": one_node_factory(x) for x in sqla_models},
        **{f"all{snake_to_camel(to_plural(get_table_name(x)))}": many_node_factory(x) for x in sqla_models},
    }

    query_object = ObjectType(name="Query", fields=lambda: query_fields)
    return query_object
