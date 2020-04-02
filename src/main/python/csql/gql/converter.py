# pylint: disable=invalid-name
from __future__ import annotations

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
from sqlalchemy import types
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import RelationshipProperty
from stringcase import pascalcase

from .registry import get_registry
from .relay import NodeInterface, global_id_field

F = GraphQLField
L = GraphQLList
NN = GraphQLNonNull


CursorType = GraphQLScalarType(name="Cursor", serialize=str)  # pylint: disable=invalid-name
DateTimeType = GraphQLScalarType(name="DateTime", serialize=str)  # pylint: disable=invalid-name

PageInfoType = GraphQLObjectType(  # pylint: disable=invalid-name
    "PageInfo",
    fields={
        "hasNextPage": F(NN(GraphQLBoolean)),
        "hasPreviousPage": F(NN(GraphQLBoolean)),
        "startCursor": F(NN(CursorType)),
        "endCursor": F(NN(CursorType)),
    },
)


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
    from csql.sql.sql_database import TableBase
    from .registry import Registry


def convert_column(
    column, output_type: Union[GraphQLField, GraphQLInputObjectField] = GraphQLField
):
    """Converts a sqlalchemy column into a graphql field or input field"""
    gql_type = GraphQLString if column.name != "id" else typemap[type(column.type)]
    notnull = not (column.nullable or False)
    return_type = NN(gql_type) if notnull else gql_type
    return output_type(return_type)


def convert_relationship(
    relationship: RelationshipProperty, registry: Registry, **field_kwargs
) -> Tuple[GraphQLField, GraphQLField]:

    """Converts a sqlalchemy relationship into a graphql connection"""
    from sqlalchemy.orm import interfaces

    direction = relationship.direction
    to_model = relationship.mapper.class_
    model_connection = registry.sqla_to_connection[to_model]

    # If this model has 1 counterpart, do not use a list
    if direction == interfaces.MANYTOONE:
        return F(NN(model_connection))

    # If this model could have multiple counterparts, use a list
    elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
        return F(L(model_connection))
    raise NotImplementedError("Bad relationship")


def convert_composite(composite):
    """Converts a sqlalchemy composite field into a graphql object type"""
    composite = composite
    raise NotImplementedError("Composite fields are not yet supported")


def table_to_model(sqla_model: TableBase) -> GraphQLObjectType:
    result_name = pascalcase(sqla_model.__table__.name)
    registry = get_registry()

    def build_attrs():
        attrs = {}
        for column in sqla_model.columns:
            attrs[column.name] = convert_column(column)

        # TODO(OR): Not the correct key
        for relationship in sqla_model.relationships:
            # TODO(OR): Make suffix depend on columns used in fkey
            attrs[relationship.key + "ById"] = F(NN(registry.sqla_to_connection[sqla_model]))
            # convert_relationship(relationship)

        # Override id to relay standard
        attrs["id"] = global_id_field(result_name)
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


def table_to_condition(sqla_model: TableBase) -> GraphQLInputObjectType:
    result_name = f"{pascalcase(sqla_model.__table__.name)}Condition"
    attrs = {}
    for column in sqla_model.columns:
        attrs[column.name] = convert_column(column, output_type=GraphQLInputObjectField)
    return GraphQLInputObjectType(result_name, attrs, description="", container_type=None)


def table_to_edge(sqla_model: TableBase) -> GraphQLObjectType:
    result_name = f"{pascalcase(sqla_model.__table__.name)}Edge"
    sqla_model_type = sqla_model
    registry = get_registry()

    def build_attrs():
        return {"cursor": F(CursorType), "node": F(registry.sqla_to_model[sqla_model_type])}

    return GraphQLObjectType(name=result_name, fields=build_attrs, description="")


def table_to_connection(sqla_model: TableBase) -> GraphQLObjectType:
    result_name = f"{pascalcase(sqla_model.__table__.name)}Connection"
    sqla_model_type = sqla_model
    registry = get_registry()

    def build_attrs():
        return {
            "nodes": F(NN(L(registry.sqla_to_model[sqla_model_type]))),
            "edges": F(NN(L(NN(registry.sqla_to_edge[sqla_model_type])))),
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


def convert_table(sqla_model: TableBase) -> GraphQLObjectType:
    # Model
    # ModelCondition
    # ModelEdge
    # ModelConnection
    # ModelOrderBy
    # ModelInput
    # ModelPatch

    sqla_model_type = sqla_model
    registry = get_registry()

    # type Model
    model = table_to_model(sqla_model)
    registry.sqla_to_model[sqla_model_type] = model
    registry.model_name_to_sqla[model.name] = sqla_model

    # input ModelCondition
    registry.sqla_to_condition[sqla_model_type] = table_to_condition(sqla_model)

    # type ModelEdge
    registry.sqla_to_edge[sqla_model_type] = table_to_edge(sqla_model)

    # type ModelConnection
    registry.sqla_to_connection[sqla_model_type] = table_to_connection(sqla_model)

    # enum ModelOrderBy
    registry.sqla_to_order_by[sqla_model_type] = table_to_order_by(sqla_model)

    return model


async def resolver_query_all(obj, info, **user_kwargs) -> List[TableBase]:
    context = info.context
    # database = context["database"]
    session = context["session"]()
    return_type = info.return_type
    registry = get_registry()

    sqla_type = [k for k, v in registry.sqla_to_connection.items() if v == return_type][0]
    # query = sqla_type.__table__.select()
    # sqla_result = await database.fetch_all(query)
    sqla_result = session.query(sqla_type).all()

    result = {
        "pageInfo": {
            "hasNextPage": False,
            "hasPreviousPage": False,
            "startCursor": "Unknown",
            "endCursor": "Unknown",
        }
    }
    result["nodes"] = sqla_result
    return result


def table_to_query_all(sqla_model: TableBase) -> GraphQLObjectType:
    sqla_model_type = sqla_model
    registry = get_registry()
    model_connection = registry.sqla_to_connection[sqla_model_type]
    model_order_by = registry.sqla_to_order_by[sqla_model_type]
    model_condition = registry.sqla_to_condition[sqla_model_type]

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
        resolver=resolver_query_all,
    )
