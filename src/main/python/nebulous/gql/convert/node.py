from __future__ import annotations

import typing
from functools import partial

from ..alias import ID, Field, InterfaceType, NonNull
from ..string_encoding import from_base64, to_base64
from .base import TableToGraphQLField

if typing.TYPE_CHECKING:
    from nebulous.sql.table_base import TableBase


def to_global_id(sqla_model, _id):
    """
    Takes a type name and an ID specific to that type name, and returns a
    "global ID" that is unique among all types.
    """
    return to_base64(":".join([sqla_model.__table__.name, str(_id)]))


def from_global_id(tables: typing.Dict[str, TableBase], global_id: str):
    """
    Takes the "global ID" created by toGlobalID, and returns the type name and ID
    used to create it.
    """
    unbased_global_id = from_base64(global_id)
    _type, _id = unbased_global_id.split(":", 1)
    return tables[_type], _id


NodeInterface = InterfaceType(
    "Node",
    description="An object with a nodeId",
    fields={
        "nodeId": Field(NonNull(ID), description="The global id of the object.", resolver=None)
    },
    # Maybe not necessary
    resolve_type=lambda *args, **kwargs: None,
)


class NodeID(TableToGraphQLField):

    type_name = "ID"

    @property
    def _type(self):
        sqla_model = self.sqla_model
        metadata = sqla_model.metadata
        tables_dict = metadata.tables

        parse_value = partial(from_global_id, tables=tables_dict)

        # TODO(OR): This is pretty flipping hacky
        # NodeInterface.fields['nodeId'].resolver = parse_value
        ID.parse_value = parse_value
        ID.parse_literal = lambda x: parse_value(global_id=x.value)
        return ID

    def _resolver(self, obj, info, **args):
        # sqla_model = self.sqla_model
        return to_global_id(obj, obj.id)
