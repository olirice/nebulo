from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Union

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
from sqlalchemy import types
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import RelationshipProperty
from stringcase import pascalcase

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
    # TSVectorType: GraphQLString,
    # Can do better
    types.DateTime: GraphQLString,
    # Add remaining
}


F = GraphQLField
L = GraphQLList
NN = GraphQLNonNull


# Relay Stuff

if TYPE_CHECKING:
    from csql.sql.sql_database import TableBase


def get_node(global_id, _info):
    """Function to map from a global id to an underlying object
    _info.context['session'] must exist
    """
    type_, id_ = from_global_id(global_id)
    print(type_, id_)
    sqla_model = model_name_to_sqla[type_]
    context = _info.context
    # Database session
    session = context["session"]

    return session.query(sqla_model).filter(sqla_model.id == id_).one_or_none()


def get_node_type(obj, _info):
    """Function to map from an underlying object to the concrete GraphQLObjectType"""
    return sqla_to_model[type(obj)]


node_interface, node_field = node_definitions(get_node, get_node_type)


def convert_column(
    column, output_type: Union[GraphQLField, GraphQLInputObjectField] = GraphQLField
):
    gql_type = GraphQLString if column.name != "id" else typemap[type(column.type)]
    notnull = not (column.nullable or False)
    return_type = NN(gql_type) if notnull else gql_type
    return output_type(return_type)


def convert_relationship(
    relationship: RelationshipProperty, **field_kwargs
) -> Tuple[GraphQLField, GraphQLField]:
    from sqlalchemy.orm import interfaces

    # from graphql_relay.connection.connection import (
    #    connection_args,
    #    connection_definitions,
    # )

    direction = relationship.direction
    to_model = relationship.mapper.class_
    # to_type = sqla_to_model[to_model]

    model_connection = sqla_to_connection[to_model]

    # This should only be getting resolved once all tables are registered
    # so it should not fail
    # model_edge, model_connection = connection_definitions(relationship.key, to_type)

    # If this model has 1 counterpart, do not use a list
    if direction == interfaces.MANYTOONE:
        return F(NN(model_connection))

    # If this model could have multiple counterparts, use a list
    elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
        return F(L(model_connection))

    raise NotImplementedError("Bad relationship")


def convert_composite(composite):
    pass


model_name_to_sqla = {}

sqla_to_model = {}
sqla_to_condition = {}
sqla_to_connection = {}
sqla_to_edge = {}
sqla_to_order_by = {}
# sqla_to_gql_input = {}
# sqla_to_gql_patch = {}

CursorType = GraphQLScalarType(name="Cursor", serialize=str)
DateTimeType = GraphQLScalarType(name="DateTime", serialize=str)

PageInfoType = GraphQLObjectType(
    "PageInfo",
    fields={
        "hasNextPage": F(NN(GraphQLBoolean)),
        "hasPreviousPage": F(NN(GraphQLBoolean)),
        "startCursor": F(NN(CursorType)),
        "endCursor": F(NN(CursorType)),
    },
)


def table_to_model(sqla_model: TableBase) -> GraphQLObjectType:
    result_name = pascalcase(sqla_model.__table__.name)

    def build_attrs():
        attrs = {}
        for column in sqla_model.columns:
            attrs[column.name] = convert_column(column)

        # TODO(OR): Not the correct key
        for relationship in sqla_model.relationships:
            # TODO(OR): Make suffix depend on columns used in fkey
            attrs[relationship.key + "ById"] = F(NN(sqla_to_connection[sqla_model]))
            # convert_relationship(relationship)

        # Override id to relay standard
        attrs["id"] = global_id_field(result_name)
        return attrs

    model = GraphQLObjectType(
        name=result_name,
        # Defer fields so tables will be registered
        # before relationships are resolved
        fields=build_attrs,
        interfaces=[node_interface],
        description="",
    )
    return model


def table_to_condition(sqla_model: TableBase) -> GraphQLInputObjectType:
    result_name = f"{pascalcase(sqla_model.__table__.name)}Condition"
    attrs = {}
    for column in sqla_model.columns:
        attrs[column.name] = convert_column(column, output_type=GraphQLInputObjectField)
    return GraphQLInputObjectType(result_name, attrs, description="", container_type=None)


def table_to_edge(sqla_model: TableBase) -> GraphQLObjectType:
    result_name = f"{pascalcase(sqla_model.__table__.name)}Edge"
    sqla_model_type = sqla_model

    def build_attrs():
        return {"cursor": F(CursorType), "node": F(sqla_to_model[sqla_model_type])}

    return GraphQLObjectType(name=result_name, fields=build_attrs, description="")


def table_to_connection(sqla_model: TableBase) -> GraphQLObjectType:
    result_name = f"{pascalcase(sqla_model.__table__.name)}Connection"
    sqla_model_type = sqla_model

    def build_attrs():
        return {
            "nodes": F(NN(L(sqla_to_model[sqla_model_type]))),
            "edges": F(NN(L(NN(sqla_to_edge[sqla_model_type])))),
            "pageInfo": F(NN(PageInfoType)),
            "totalCount": F(NN(GraphQLInt)),
        }

    return GraphQLObjectType(name=result_name, fields=build_attrs, description="")


def table_to_order_by(sqla_model: TableBase) -> GraphQLInputObjectType:
    result_name = f"{pascalcase(sqla_model.__table__.name)}OrderBy"
    # TODO(OR): Implement properly
    return GraphQLEnumType(
        result_name, {"ID_DESC": GraphQLEnumValue(value=("id", "desc"))}, description=""
    )


def table_to_query_all(sqla_model: TableBase) -> GraphQLObjectType:
    sqla_model_type = sqla_model
    model_connection = sqla_to_connection[sqla_model_type]
    model_order_by = sqla_to_order_by[sqla_model_type]
    model_condition = sqla_to_condition[sqla_model_type]

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
        resolver=None,
    )


def convert_table(sqla_model: TableBase) -> GraphQLObjectType:
    # Model
    # ModelCondition
    # ModelEdge
    # ModelConnection
    # ModelOrderBy
    # ModelInput
    # ModelPatch

    sqla_model_type = sqla_model

    # type Model
    model = table_to_model(sqla_model)
    sqla_to_model[sqla_model_type] = model
    model_name_to_sqla[model.name] = sqla_model

    # input ModelCondition
    sqla_to_condition[sqla_model_type] = table_to_condition(sqla_model)

    # type ModelEdge
    sqla_to_edge[sqla_model_type] = table_to_edge(sqla_model)

    # type ModelConnection
    sqla_to_connection[sqla_model_type] = table_to_connection(sqla_model)

    # enum ModelOrderBy
    sqla_to_order_by[sqla_model_type] = table_to_order_by(sqla_model)

    return model
