from __future__ import annotations

import typing

from nebulo.gql.alias import Argument, Field, NonNull, ObjectType, Schema
from nebulo.gql.convert.connection import connection_args_factory, connection_factory
from nebulo.gql.convert.function import function_factory
from nebulo.gql.convert.jwt_function import jwt_function_factory
from nebulo.gql.convert.node_interface import NodeID
from nebulo.gql.convert.table import table_factory
from nebulo.gql.resolver.asynchronous import async_resolver
from nebulo.gql.resolver.synchronous import sync_resolver
from nebulo.sql.inspect import get_table_name
from nebulo.sql.reflection.function import SQLFunction
from nebulo.text_utils import snake_to_camel, to_plural

__all__ = ["sqla_models_to_graphql_schema"]


def sqla_models_to_graphql_schema(
    sqla_models,
    sql_functions: typing.List[SQLFunction],
    resolve_async: bool = False,
    jwt_identifier: typing.Optional[str] = None,
    jwt_secret: typing.Optional[str] = None,
) -> Schema:
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
    mutation_fields = {}
    for sql_function in sql_functions:
        field_key = f"{snake_to_camel(sql_function.name, upper=False)}"

        if is_jwt_function(sql_function, jwt_identifier):
            mutation_fields[field_key] = jwt_function_factory(
                sql_function=sql_function, jwt_secret=jwt_secret, resolve_async=resolve_async
            )
        else:
            mutation_fields[field_key] = function_factory(sql_function=sql_function, resolve_async=resolve_async)

    mutation_object = ObjectType(name="Mutation", fields=lambda: mutation_fields)

    schema_kwargs = {}
    if len(query_fields) > 0:
        schema_kwargs["query"] = query_object

    if len(mutation_fields) > 0:
        schema_kwargs["mutation"] = mutation_object

    return Schema(**schema_kwargs)


def is_jwt_function(sql_function: SQLFunction, jwt_identifier: typing.Optional[str]):
    function_return_type_identifier = sql_function.return_pg_type_schema + "." + sql_function.return_pg_type
    return function_return_type_identifier == jwt_identifier
