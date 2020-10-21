from __future__ import annotations

import typing

from nebulo.config import Config
from nebulo.gql.alias import ObjectType, Schema
from nebulo.gql.convert.connection import connection_field_factory
from nebulo.gql.convert.create import create_entrypoint_factory
from nebulo.gql.convert.delete import delete_entrypoint_factory
from nebulo.gql.convert.function import (
    immutable_function_entrypoint_factory,
    is_jwt_function,
    mutable_function_entrypoint_factory,
)
from nebulo.gql.convert.table import table_field_factory
from nebulo.gql.convert.update import update_entrypoint_factory
from nebulo.gql.resolve.resolvers.asynchronous import async_resolver as resolver
from nebulo.sql.inspect import get_table_name
from nebulo.sql.reflection.function import SQLFunction
from nebulo.text_utils import snake_to_camel, to_plural

__all__ = ["sqla_models_to_graphql_schema"]


def sqla_models_to_graphql_schema(
    sqla_models,
    sql_functions: typing.Optional[typing.List[SQLFunction]] = None,
    jwt_identifier: typing.Optional[str] = None,
    jwt_secret: typing.Optional[str] = None,
) -> Schema:
    """Creates a GraphQL Schema from SQLA Models

    **Parameters**

    * **sqla_models**: _List[Type[SQLAModel]]_ = List of SQLAlchemy models to include in the GraphQL schema
    * **jwt_identifier**: _str_ = qualified path of SQL composite type to use encode as a JWT e.g. 'public.jwt'
    * **jwt_secret**: _str_ = Secret key used to encrypt JWT contents
    * **sql_functions** = **NOT PUBLIC API**
    """

    if sql_functions is None:
        sql_functions = []

    query_fields = {}
    mutation_fields = {}

    # Tables
    for sqla_model in sqla_models:

        if not Config.exclude_read_one(sqla_model):
            # e.g. account(nodeId: NodeID)
            single_name = snake_to_camel(get_table_name(sqla_model), upper=False)
            query_fields[single_name] = table_field_factory(sqla_model, resolver)

        if not Config.exclude_read_all(sqla_model):
            # e.g. allAccounts(first: Int, last: Int ....)
            connection_name = "all" + snake_to_camel(to_plural(get_table_name(sqla_model)), upper=True)
            query_fields[connection_name] = connection_field_factory(sqla_model, resolver)

        if not Config.exclude_create(sqla_model):
            # e.g. createAccount(input: CreateAccountInput)
            mutation_fields.update(create_entrypoint_factory(sqla_model, resolver=resolver))

        if not Config.exclude_update(sqla_model):
            # e.g. updateAccount(input: UpdateAccountInput)
            mutation_fields.update(update_entrypoint_factory(sqla_model, resolver=resolver))

        if not Config.exclude_delete(sqla_model):
            # e.g. deleteAccount(input: DeleteAccountInput)
            mutation_fields.update(delete_entrypoint_factory(sqla_model, resolver=resolver))
    # Functions
    for sql_function in sql_functions:
        if is_jwt_function(sql_function, jwt_identifier):
            mutation_fields.update(
                mutable_function_entrypoint_factory(sql_function=sql_function, resolver=resolver, jwt_secret=jwt_secret)
            )
        else:

            # Immutable functions are queries
            if sql_function.is_immutable:
                query_fields.update(immutable_function_entrypoint_factory(sql_function=sql_function, resolver=resolver))

            # Mutable functions are mutations
            else:
                mutation_fields.update(
                    mutable_function_entrypoint_factory(sql_function=sql_function, resolver=resolver)
                )

    schema_kwargs = {
        "query": ObjectType(name="Query", fields=query_fields),
        "mutation": ObjectType(name="Mutation", fields=mutation_fields),
    }
    return Schema(**{k: v for k, v in schema_kwargs.items() if v.fields})
