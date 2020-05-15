from __future__ import annotations

import typing

from nebulo.gql.alias import ObjectType, Schema
from nebulo.gql.convert.connection import connection_field_factory
from nebulo.gql.convert.create import create_entrypoint_factory
from nebulo.gql.convert.function import function_factory
from nebulo.gql.convert.jwt_function import jwt_function_factory
from nebulo.gql.convert.table import table_field_factory
from nebulo.gql.convert.update import update_entrypoint_factory
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

    query_fields = {}
    mutation_fields = {}

    for sqla_model in sqla_models:
        # e.g. account(nodeId: NodeID)
        single_name = snake_to_camel(get_table_name(sqla_model), upper=False)
        query_fields[single_name] = table_field_factory(sqla_model, resolver)

        # e.g. allAccounts(first: Int, last: Int ....)
        connection_name = "all" + snake_to_camel(to_plural(get_table_name(sqla_model)), upper=True)
        query_fields[connection_name] = connection_field_factory(sqla_model, resolver)

        # e.g. createAccount(input: CreateAccountInput)
        mutation_fields.update(create_entrypoint_factory(sqla_model, resolver=resolver))
        # e.g. updateAccount(input: UpdateAccountInput)
        mutation_fields.update(update_entrypoint_factory(sqla_model, resolver=resolver))

    # Mutations
    for sql_function in sql_functions:
        field_key = f"{snake_to_camel(sql_function.name, upper=False)}"

        if is_jwt_function(sql_function, jwt_identifier):
            mutation_fields[field_key] = jwt_function_factory(
                sql_function=sql_function, jwt_secret=jwt_secret, resolve_async=resolve_async
            )
        else:
            mutation_fields[field_key] = function_factory(sql_function=sql_function, resolve_async=resolve_async)

    schema_kwargs = {}
    if len(query_fields) > 0:
        schema_kwargs["query"] = ObjectType(name="Query", fields=lambda: query_fields)

    if len(mutation_fields) > 0:
        schema_kwargs["mutation"] = ObjectType(name="Mutation", fields=lambda: mutation_fields)

    return Schema(**schema_kwargs)


def is_jwt_function(sql_function: SQLFunction, jwt_identifier: typing.Optional[str]):
    function_return_type_identifier = sql_function.return_pg_type_schema + "." + sql_function.return_pg_type
    return function_return_type_identifier == jwt_identifier
