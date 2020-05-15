from __future__ import annotations

from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import Field, InputObjectType, ObjectType, String
from nebulo.gql.convert.column import convert_column_to_input
from nebulo.sql.inspect import get_columns
from nebulo.sql.table_base import TableProtocol


"""
createAccount(input: CreateAccountInput!):
    CreateAccountPayload
"""


@lru_cache()
def create_entrypoint_factory(sqla_model: TableProtocol, resolver) -> Field:
    """createAccount"""
    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    name = f"create{relevant_type_name}"
    args = {"input": create_input_type_factory(sqla_model)}
    payload = create_payload_factory(sqla_model)
    return {name: Field(payload, args=args, resolve=resolver, description=f"Creates a single {relevant_type_name}.")}


@lru_cache()
def create_input_type_factory(sqla_model: TableProtocol) -> InputObjectType:
    """CreateAccountInput!"""
    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    result_name = f"Create{relevant_type_name}Input"

    input_object_name = Config.table_name_mapper(sqla_model)

    attrs = {"clientMutationId": String, input_object_name: input_type_factory(sqla_model)}
    return InputObjectType(result_name, attrs, description=f"All input for the create {relevant_type_name} mutation.")


def input_type_factory(sqla_model: TableProtocol) -> InputObjectType:
    """AccountInput"""
    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    result_name = f"{relevant_type_name}Input"

    attrs = {}
    for column in get_columns(sqla_model):
        field_key = Config.column_name_mapper(column)
        attrs[field_key] = convert_column_to_input(column)
    return InputObjectType(result_name, attrs, description=f"An input for mutations affecting {relevant_type_name}.")


@lru_cache()
def create_payload_factory(sqla_model: TableProtocol) -> InputObjectType:
    """CreateAccountPayload"""
    from nebulo.gql.convert.table import table_factory

    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    relevant_attr_name = Config.table_name_mapper(sqla_model)
    result_name = f"Create{relevant_type_name}Payload"

    attrs = {
        "clientMutationId": Field(String),
        relevant_attr_name: Field(
            table_factory(sqla_model), description=f"The {relevant_type_name} that was created by this mutation."
        ),
    }

    return ObjectType(result_name, attrs, description=f"The output of our create {relevant_type_name} mutation")
