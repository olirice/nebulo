from __future__ import annotations

from base64 import b64decode as _unbase64
from base64 import b64encode as _base64
from typing import TYPE_CHECKING

from ..alias import ID, Field, InterfaceType, NonNull
from .base import TableToGraphQLField

if TYPE_CHECKING:
    pass


# __all__ = ["global_id_field", "from_global_id", "NodeInterface", "NodeField"]


def base64(string):
    return _base64(string.encode("utf-8")).decode("utf-8")


def unbase64(string):
    return _unbase64(string).decode("utf-8")


def to_global_id(_type, _id):
    """
    Takes a type name and an ID specific to that type name, and returns a
    "global ID" that is unique among all types.
    """
    return base64(":".join([_type, str(_id)]))


def from_global_id(global_id):
    """
    Takes the "global ID" created by toGlobalID, and returns the type name and ID
    used to create it.
    """
    unbased_global_id = unbase64(global_id)
    _type, _id = unbased_global_id.split(":", 1)
    return _type, _id


NodeInterface = InterfaceType(
    "Node",
    description="An object with a nodeId",
    fields=lambda: {
        "nodeId": Field(NonNull(ID), description="The global id of the object.", resolver=None)
    },
    # Maybe not necessary
    resolve_type=lambda *args, **kwargs: None,
)


def resolver(self, global_id: str, _info):
    """Function to map from a global id to an underlying object
    _info.context['session'] must exist
    """
    _, id_ = from_global_id(global_id)
    context = _info.context
    session = context["session"]
    sqla_model = self.sqla_model
    return session.query(sqla_model).filter(sqla_model.id == id_).one_or_none()


class NodeID(TableToGraphQLField):

    type_name = "NodeID"

    _type = ID

    def resolver(self, obj, info, **args):
        sqla_model = self.sqla_model
        return to_global_id(sqla_model.__table__.name, obj.id)
