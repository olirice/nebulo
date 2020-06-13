"""
When SQL functions are marked as immutable, they are handled as queries
Otherwise, they are mutations
"""
from __future__ import annotations

import typing
from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import (
    Argument,
    Field,
    FunctionInputType,
    FunctionPayloadType,
    InputObjectType,
    NonNull,
    ObjectType,
    String,
    TableInputType,
)
from nebulo.gql.convert.column import convert_input_type, convert_type
from nebulo.gql.resolve.resolvers.default import default_resolver
from nebulo.sql.reflection.function import SQLFunction

__all__ = ["mutable_function_entrypoint_factory", "immutable_function_entrypoint_factory"]

"""
# When volatile
authenticate(input: AuthenticateInput!):
    AuthenticatePayload

# When immutable
toUpper(someText: String!):
    String
"""


@lru_cache()
def immutable_function_entrypoint_factory(
    sql_function: SQLFunction, resolver: typing.Callable
) -> typing.Dict[str, Field]:
    """authenticate"""
    # TODO(OR): need seperate mapper
    function_name = Config.function_name_mapper(sql_function)

    if not sql_function.is_immutable:
        raise Exception(f"SQLFunction {sql_function.name} is not immutable, use mutable_function_entrypoint")

    gql_args = {
        (arg_name if arg_name else f"param{ix}"): Argument(NonNull(convert_type(arg_sqla_type)))
        for ix, (arg_name, arg_sqla_type) in enumerate(zip(sql_function.arg_names, sql_function.arg_sqla_types))
    }

    return_type = convert_type(sql_function.return_sqla_type)
    return_type.sql_function = sql_function
    return_field = Field(return_type, args=gql_args, resolve=resolver, description="")

    return {function_name: return_field}


@lru_cache()
def mutable_function_entrypoint_factory(
    sql_function: SQLFunction, resolver: typing.Callable
) -> typing.Dict[str, Field]:
    """authenticate"""
    # TODO(OR): need seperate mapper
    function_name = Config.function_name_mapper(sql_function)

    if sql_function.is_immutable:
        raise Exception(f"SQLFunction {sql_function.name} is immutable, use immutable_function_entrypoint")

    args = {"input": NonNull(function_input_type_factory(sql_function))}
    payload = function_payload_factory(sql_function)
    return {
        function_name: Field(payload, args=args, resolve=resolver, description=f"Call the function {function_name}.")
    }


# Remainder relates to mutation functions


@lru_cache()
def function_input_type_factory(sql_function: SQLFunction) -> FunctionInputType:
    """AuthenticateInput!"""
    function_name = Config.function_type_name_mapper(sql_function)
    result_name = f"{function_name}Input"

    function_args = {
        (arg_name if arg_name else f"param{ix}"): NonNull(convert_input_type(arg_sqla_type))
        for ix, (arg_name, arg_sqla_type) in enumerate(zip(sql_function.arg_names, sql_function.arg_sqla_types))
    }

    attrs = {"clientMutationId": String, **function_args}
    return FunctionInputType(result_name, attrs, description=f"All input for the {function_name} mutation.")


@lru_cache()
def function_payload_factory(sql_function: SQLFunction) -> FunctionPayloadType:
    """CreateAccountPayload"""
    function_name = Config.function_type_name_mapper(sql_function)
    result_name = f"{function_name}Payload"

    # TODO(OR): handle functions with no return
    function_return_type = convert_type(sql_function.return_sqla_type)
    function_return_type.sql_function = sql_function

    attrs = {
        "clientMutationId": Field(String, resolve=default_resolver),
        "result": Field(
            NonNull(function_return_type),
            description=f"The {result_name} that was created by this mutation.",
            resolve=default_resolver,
        ),
    }

    return FunctionPayloadType(result_name, attrs, description=f"The output of our create {function_name} mutation")
