from __future__ import annotations

from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import Field, InputObjectType, ObjectType, String
from nebulo.gql.convert.column import convert_column_to_input
from nebulo.gql.convert.node_interface import NodeID
from nebulo.sql.inspect import get_columns
from nebulo.sql.table_base import TableProtocol


"""
updateAccount(input: UpdateAccountInput!):
    UpdateAccountPayload
"""


@lru_cache()
def update_entrypoint_factory(sqla_model: TableProtocol, resolver) -> Field:
    """updateAccount"""
    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    name = f"update{relevant_type_name}"
    args = {"input": update_input_type_factory(sqla_model)}
    payload = update_payload_factory(sqla_model)
    return {
        name: Field(
            payload,
            args=args,
            resolve=resolver,
            description=f"Updates a single {relevant_type_name} using its globally unique id and a patch.",
        )
    }


@lru_cache()
def update_input_type_factory(sqla_model: TableProtocol) -> InputObjectType:
    """UpdateAccountInput!"""
    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    result_name = f"Update{relevant_type_name}Input"

    input_object_name = Config.table_name_mapper(sqla_model)

    attrs = {"nodeId": NodeID, "clientMutationId": String, input_object_name: patch_type_factory(sqla_model)}
    return InputObjectType(result_name, attrs, description=f"All input for the create {relevant_type_name} mutation.")


def patch_type_factory(sqla_model: TableProtocol) -> InputObjectType:
    """AccountPatch"""
    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    result_name = f"{relevant_type_name}Patch"

    attrs = {}
    for column in get_columns(sqla_model):
        field_key = Config.column_name_mapper(column)
        column_field = convert_column_to_input(column)
        # TODO Unwrap not null here
        attrs[field_key] = column_field
    return InputObjectType(result_name, attrs, description=f"An input for mutations affecting {relevant_type_name}.")


@lru_cache()
def update_payload_factory(sqla_model: TableProtocol) -> InputObjectType:
    """UpdateAccountPayload"""
    from nebulo.gql.convert.table import table_factory

    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    relevant_attr_name = Config.table_name_mapper(sqla_model)
    result_name = f"Update{relevant_type_name}Payload"

    attrs = {
        "clientMutationId": Field(String),
        relevant_attr_name: Field(
            table_factory(sqla_model), description=f"The {relevant_type_name} that was created by this mutation."
        ),
    }

    return ObjectType(result_name, attrs, description=f"The output of our update {relevant_type_name} mutation")