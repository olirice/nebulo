# pylint: disable=invalid-name
from __future__ import annotations

from functools import lru_cache, partial
from typing import TYPE_CHECKING, List, Union

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
from graphql.pyutils.convert_case import snake_to_camel  # camel_to_snake, snake_to_camel
from sqlalchemy import types
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import RelationshipProperty, interfaces

from .convert.connection import Connection
from .convert.node import NodeID, NodeInterface
from .convert.page_info import CursorType

F = GraphQLField
L = GraphQLList
NN = GraphQLNonNull


DateTimeType = GraphQLScalarType(name="DateTime", serialize=str)  # pylint: disable=invalid-name

typemap = {
    types.Integer: GraphQLInt,
    types.INTEGER: GraphQLInt,
    types.Date: GraphQLString,
    types.Time: GraphQLString,
    types.String: GraphQLString,
    types.Text: GraphQLString,
    types.Unicode: GraphQLString,
    types.UnicodeText: GraphQLString,
    postgresql.UUID: GraphQLString,
    postgresql.INET: GraphQLString,
    postgresql.CIDR: GraphQLString,
    types.DateTime: GraphQLString,
}


if TYPE_CHECKING:
    from nebulous.sql.table_base import TableBase


@lru_cache()
def convert_column(
    column, output_type: Union[GraphQLField, GraphQLInputObjectField] = GraphQLField
):
    """Converts a sqlalchemy column into a graphql field or input field"""
    gql_type = GraphQLString if column.name != "id" else typemap[type(column.type)]
    notnull = not (column.nullable or False)
    return_type = NN(gql_type) if notnull else gql_type
    return output_type(return_type)


@lru_cache()
def convert_composite(composite):
    """Converts a sqlalchemy composite field into a graphql object type"""
    composite = composite
    raise NotImplementedError("Composite fields are not yet supported")


def relationship_is_nullable(relationship: RelationshipProperty) -> bool:
    """Checks if a sqlalchemy orm relationship is nullable"""
    return not any([col.nullable for col in relationship.local_columns])


def relationship_to_attr_name(relationship: RelationshipProperty) -> str:
    """ """
    return (
        relationship.key
        + "By"
        + "And".join([snake_to_camel(col.name) for col in relationship.local_columns])
    )


def resolve_model_via_relationship(
    obj, info, sqla_model: TableBase, relationship_key: str, **user_kwargs
) -> List[TableBase]:
    result = getattr(obj, relationship_key, None)
    return result


@lru_cache()
def table_to_model(sqla_model: TableBase) -> GraphQLObjectType:
    result_name = snake_to_camel(sqla_model.__table__.name)

    node_id = NodeID(sqla_model)

    def build_attrs():
        attrs = {}

        # Override id to relay standard
        attrs["nodeId"] = F(NN(node_id.type), resolver=node_id.resolver)

        for column in sqla_model.columns:
            attrs[column.name] = convert_column(column)

        for relationship in sqla_model.relationships:

            direction = relationship.direction
            to_sqla_model = relationship.mapper.class_

            is_nullable = relationship_is_nullable(relationship)

            # Name of the attribute on the model
            attr_key = relationship_to_attr_name(relationship)

            resolver = partial(
                resolve_model_via_relationship,
                sqla_model=sqla_model,
                relationship_key=relationship.key,
            )

            # TODO(OR): Update so key is set by relevant fields

            # If this model has 1 counterpart, do not use a list
            if direction == interfaces.MANYTOONE:
                to_model = table_to_model(to_sqla_model)
                maybe_null_model = to_model if is_nullable else NN(to_model)
                attrs[attr_key] = F(maybe_null_model, resolver=resolver)

            elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
                model_connection = Connection(to_sqla_model)
                model_connection_type = model_connection.type
                maybe_null_connection = (
                    model_connection_type if is_nullable else NN(model_connection_type)
                )
                attrs[attr_key] = F(maybe_null_connection, resolver=model_connection.resolver)

        return attrs

    model = GraphQLObjectType(
        name=result_name,
        # Defer fields so tables will be registered
        # before relationships are resolved
        fields=build_attrs,
        interfaces=[NodeInterface],
        description="",
    )
    return model


@lru_cache()
def table_to_condition(sqla_model: TableBase) -> GraphQLInputObjectType:
    result_name = f"{snake_to_camel(sqla_model.__table__.name)}Condition"
    attrs = {}
    for column in sqla_model.columns:
        attrs[column.name] = convert_column(column, output_type=GraphQLInputObjectField)
    return GraphQLInputObjectType(result_name, attrs, description="", container_type=None)


@lru_cache()
def table_to_order_by(sqla_model: TableBase) -> GraphQLInputObjectType:
    result_name = f"{snake_to_camel(sqla_model.__table__.name)}OrderBy"
    # TODO(OR): Implement properly
    return GraphQLEnumType(
        result_name, {"ID_DESC": GraphQLEnumValue(value=("id", "desc"))}, description=""
    )


@lru_cache()
def table_to_query_all(sqla_model: TableBase) -> GraphQLObjectType:
    model_connection = Connection(sqla_model)
    model_order_by = table_to_order_by(sqla_model)
    model_condition = table_to_condition(sqla_model)

    return F(
        model_connection.type,
        args={
            "first": GraphQLArgument(GraphQLInt, default_value=10, description="", out_name=None),
            "last": GraphQLArgument(GraphQLInt),
            "offset": GraphQLArgument(GraphQLInt, description="Alternative to cursor pagination"),
            "before": GraphQLArgument(CursorType),
            "after": GraphQLArgument(CursorType),
            "orderBy": GraphQLArgument(L(NN(model_order_by)), default_value=["ID_DESC"]),
            "condition": GraphQLArgument(model_condition),
        },
        resolver=model_connection.resolver,
    )
