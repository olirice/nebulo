from __future__ import annotations

from graphql import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLID,
    GraphQLInputObjectField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
)
from graphql_relay.node.node import from_global_id, global_id_field, node_definitions

from .converter import get_registry

### RELAY ###
__all__ = ["global_id_field", "from_global_id", "NodeInterface", "NodeField"]


def get_node(global_id, _info):
    """Function to map from a global id to an underlying object
    _info.context['session'] must exist
    """
    registry = get_registry()
    type_, id_ = from_global_id(global_id)
    sqla_model = registry.model_name_to_sqla[type_]
    context = _info.context
    # Database session
    session = context["session"]
    return session.query(sqla_model).filter(sqla_model.id == id_).one_or_none()


def get_node_type(obj, _info):
    """Function to map from an underlying object to the concrete GraphQLObjectType"""
    registry = get_registry()
    return registry.sqla_to_model[type(obj)]


NodeInterface, NodeField = node_definitions(get_node, get_node_type)  # pylint: disable=invalid-name
