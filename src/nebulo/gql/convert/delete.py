from __future__ import annotations

from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import (
    DeleteInputType,
    DeletePayloadType,
    Field,
    InputObjectType,
    NonNull,
    ObjectType,
    String,
    TableInputType,
)
from nebulo.gql.relay.node_interface import ID
from nebulo.gql.resolve.resolvers.default import default_resolver
from nebulo.sql.table_base import TableProtocol

"""
deleteAccount(input: DeleteAccountInput!):
    deleteAccountPayload
"""


@lru_cache()
def delete_entrypoint_factory(sqla_model: TableProtocol, resolver) -> Field:
    """deleteAccount"""
    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    name = f"delete{relevant_type_name}"
    args = {"input": NonNull(delete_input_type_factory(sqla_model))}
    payload = delete_payload_factory(sqla_model)
    return {
        name: Field(
            payload,
            args=args,
            resolve=resolver,
            description=f"Delete a single {relevant_type_name} using its globally unique id and a patch.",
        )
    }


@lru_cache()
def delete_input_type_factory(sqla_model: TableProtocol) -> InputObjectType:
    """DeleteAccountInput!"""
    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    result_name = f"Delete{relevant_type_name}Input"

    input_object_name = Config.table_name_mapper(sqla_model)

    attrs = {
        "nodeId": NonNull(ID),
        "clientMutationId": String,
    }
    return DeleteInputType(result_name, attrs, description=f"All input for the create {relevant_type_name} mutation.")


@lru_cache()
def delete_payload_factory(sqla_model: TableProtocol) -> InputObjectType:
    """DeleteAccountPayload"""

    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    result_name = f"Delete{relevant_type_name}Payload"

    attrs = {"clientMutationId": Field(String, resolve=default_resolver), "nodeId": ID}

    return DeletePayloadType(
        result_name, attrs, description=f"The output of our delete {relevant_type_name} mutation", sqla_model=sqla_model
    )
