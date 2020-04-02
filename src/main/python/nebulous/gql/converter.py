# pylint: disable=invalid-name
from __future__ import annotations

from functools import lru_cache, partial
from typing import TYPE_CHECKING, List, Tuple, Union

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
from sqlalchemy.orm import RelationshipProperty

from .convert.node import NodeID, NodeInterface
from .convert.page_info import CursorType, PageInfo

# from .relay import NodeInterface, global_id_field


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
def convert_relationship(
    relationship: RelationshipProperty, **field_kwargs
) -> Tuple[GraphQLField, GraphQLField]:

    """Converts a sqlalchemy relationship into a graphql connection"""
    from sqlalchemy.orm import interfaces

    direction = relationship.direction
    to_model = relationship.mapper.class_
    model_connection = table_to_connection(to_model)

    # If this model has 1 counterpart, do not use a list
    if direction == interfaces.MANYTOONE:
        return F(NN(model_connection))

    # If this model could have multiple counterparts, use a list
    elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
        return F(L(model_connection))
    raise NotImplementedError("Bad relationship")


@lru_cache()
def convert_composite(composite):
    """Converts a sqlalchemy composite field into a graphql object type"""
    composite = composite
    raise NotImplementedError("Composite fields are not yet supported")


@lru_cache()
def table_to_model(sqla_model: TableBase) -> GraphQLObjectType:
    result_name = snake_to_camel(sqla_model.__table__.name)

    node_id = NodeID(sqla_model)

    def build_attrs():
        attrs = {}
        for column in sqla_model.columns:
            attrs[column.name] = convert_column(column)

        for relationship in sqla_model.relationships:
            # TODO(OR): Make suffix depend on columns used in fkey
            attrs[relationship.key + "ById"] = F(NN(table_to_connection(sqla_model)))
            # convert_relationship(relationship)

        # Override id to relay standard
        attrs["nodeId"] = F(NN(node_id.type), resolver=node_id.resolver)
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
def table_to_edge(sqla_model: TableBase) -> GraphQLObjectType:
    result_name = f"{snake_to_camel(sqla_model.__table__.name)}Edge"

    def build_attrs():
        return {"cursor": F(CursorType), "node": F(table_to_model(sqla_model))}

    return GraphQLObjectType(name=result_name, fields=build_attrs, description="")


@lru_cache()
def table_to_connection(sqla_model: TableBase) -> GraphQLObjectType:
    result_name = f"{snake_to_camel(sqla_model.__table__.name)}Connection"

    page_info = PageInfo(sqla_model)

    def build_attrs():
        return {
            "nodes": F(
                NN(L(table_to_model(sqla_model))),
                resolver=None,  # lambda *x, **y: print("nodes", x, y),
            ),
            "edges": F(
                NN(L(NN(table_to_edge(sqla_model)))), resolver=lambda *x, **y: print("edges", x, y)
            ),
            "pageInfo": F(NN(page_info.type), resolver=page_info.resolver),
            "totalCount": F(NN(GraphQLInt), resolver=lambda *x, **y: 1),
        }

    return GraphQLObjectType(name=result_name, fields=build_attrs, description="")


@lru_cache()
def table_to_order_by(sqla_model: TableBase) -> GraphQLInputObjectType:
    result_name = f"{snake_to_camel(sqla_model.__table__.name)}OrderBy"
    # TODO(OR): Implement properly
    return GraphQLEnumType(
        result_name, {"ID_DESC": GraphQLEnumValue(value=("id", "desc"))}, description=""
    )


@lru_cache()
def table_to_query_all(sqla_model: TableBase) -> GraphQLObjectType:
    model_connection = table_to_connection(sqla_model)
    model_order_by = table_to_order_by(sqla_model)
    model_condition = table_to_condition(sqla_model)

    return F(
        model_connection,
        args={
            "first": GraphQLArgument(GraphQLInt, default_value=10, description="", out_name=None),
            "last": GraphQLArgument(GraphQLInt),
            "offset": GraphQLArgument(GraphQLInt, description="Alternative to cursor pagination"),
            "before": GraphQLArgument(CursorType),
            "after": GraphQLArgument(CursorType),
            "orderBy": GraphQLArgument(L(NN(model_order_by)), default_value=["ID_DESC"]),
            "condition": GraphQLArgument(model_condition),
        },
        resolver=partial(resolver_query_all, sqla_model=sqla_model),
        # resolver=None,
    )


def resolver_query_all(obj, info, sqla_model: TableBase, **user_kwargs) -> List[TableBase]:
    print("Query all resolver", user_kwargs, obj)
    """Genric resolver for queries of type"""
    context = info.context
    session = context["session"]()
    return_type = info.return_type

    # TODO(OR): Fix
    sqla_result = session.query(sqla_model).all()

    # result = {
    #    "pageInfo":
    # }
    result = {}
    result["nodes"] = sqla_result
    return result
