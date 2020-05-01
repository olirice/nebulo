from __future__ import annotations

import json

from nebulo.gql.alias import Argument, Field, NonNull, ObjectType, ResolveInfo, Schema
from nebulo.gql.convert.connection import connection_args_factory, connection_factory
from nebulo.gql.convert.function import function_factory
from nebulo.gql.convert.node_interface import NodeID
from nebulo.gql.convert.table import table_factory
from nebulo.gql.parse_info import parse_resolve_info
from nebulo.gql.query_builder import sql_builder, sql_finalize
from nebulo.sql.inspect import get_table_name
from nebulo.text_utils import snake_to_camel, to_plural

__all__ = ["sqla_models_to_graphql_schema"]


def sqla_models_to_graphql_schema(sqla_models, sql_functions, resolve_async: bool = False) -> Schema:
    """Creates a GraphQL Schema from SQLA Models"""

    resolver = async_resolver if resolve_async else sync_resolver

    def many_node_factory(sqla_model) -> Field:
        connection = connection_factory(sqla_model)
        return Field(connection, args=connection_args_factory(sqla_model), resolve=resolver, description="")

    def one_node_factory(sqla_model) -> Field:
        node = table_factory(sqla_model)
        return Field(node, args={"nodeId": Argument(NonNull(NodeID))}, resolve=resolver, description="")

    # Queries
    query_fields = {
        **{f"{snake_to_camel(get_table_name(x), upper=False)}": one_node_factory(x) for x in sqla_models},
        **{f"all{snake_to_camel(to_plural(get_table_name(x)))}": many_node_factory(x) for x in sqla_models},
    }
    query_object = ObjectType(name="Query", fields=lambda: query_fields)

    # Mutations
    mutation_fields = {**{f"{snake_to_camel(x.name, upper=False)}": function_factory(x) for x in sql_functions}}
    mutation_object = ObjectType(name="Mutation", fields=lambda: mutation_fields)

    schema_kwargs = {}
    if len(query_fields) > 0:
        schema_kwargs["query"] = query_object

    if len(mutation_fields) > 0:
        schema_kwargs["mutation"] = mutation_object

    return Schema(**schema_kwargs)


def sync_resolver(_, info: ResolveInfo, **kwargs):
    """GraphQL Entrypoint resolver

    Expects:
        info.context['session'] to contain a sqlalchemy.orm.Session
    """

    context = info.context
    session = context["session"]
    tree = parse_resolve_info(info)
    query = sql_finalize(tree.name, sql_builder(tree))
    result = session.execute(query).fetchone()[0]
    # Stash result on context to enable dumb resolvers to not fail
    context["result"] = result
    return result


async def async_resolver(_, info: ResolveInfo, **kwargs):
    """Awaitable GraphQL Entrypoint resolver

    Expects:
        info.context['database'] to contain a databases.Database
    """
    context = info.context
    database = context["database"]
    tree = parse_resolve_info(info)
    query: str = sql_finalize(tree.name, sql_builder(tree))
    str_result: str = (await database.fetch_one(query=query))["jsonb_build_object"]
    result = json.loads(str_result)
    # Stash result on context to enable dumb resolvers to not fail
    context["result"] = result
    return result
