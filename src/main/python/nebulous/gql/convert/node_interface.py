from __future__ import annotations

import typing

import sqlalchemy
from sqlalchemy import cast, literal

from ..alias import Field, InterfaceType, NonNull, ScalarType
from ..string_encoding import from_base64, to_base64, to_encoding_in_sql

if typing.TYPE_CHECKING:
    pass


def to_global_id(name, _id):
    """
    Takes a type name and an ID specific to that type name, and returns a
    "global ID" that is unique among all types.
    """
    return to_base64(":".join([name, str(_id)]))


def from_global_id(global_id: str):
    """
    Takes the "global ID" created by toGlobalID, and returns the type name and ID
    used to create it.
    """
    try:
        unbased_global_id = from_base64(global_id)
        _type, _id = unbased_global_id.split(":", 1)
        _id = int(_id)
    except Exception as exc:
        raise ValueError(f"Bad input: invalid NodeID {global_id}")
    return _type, _id


NodeID = ScalarType(
    "NodeID",
    description="Unique ID for node",
    serialize=str,
    parse_value=from_global_id,
    parse_literal=lambda x: from_global_id(global_id=x.value),
)

NodeInterface = InterfaceType(
    "NodeInterface",
    description="An object with a nodeId",
    fields={
        "nodeId": Field(NonNull(NodeID), description="The global id of the object.", resolver=None)
    },
    # Maybe not necessary
    resolve_type=lambda *args, **kwargs: None,
)


def resolve_node_id(query, sqla_model):
    return to_encoding_in_sql(
        literal(sqla_model.__table__.name) + literal(":") + cast(query.c.id, sqlalchemy.String())
    )
