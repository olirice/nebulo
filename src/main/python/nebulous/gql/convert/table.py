# pylint: disable=invalid-name
from __future__ import annotations

import typing
from functools import lru_cache

import sqlalchemy
from sqlalchemy import cast, func, select, types
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import RelationshipProperty, interfaces
from sqlalchemy.sql.expression import literal

from ..alias import (
    Argument,
    EnumType,
    EnumValue,
    Field,
    InputField,
    InputObjectType,
    Int,
    List,
    NonNull,
    ObjectType,
    ResolveInfo,
    ScalarType,
    String,
    TableType,
)
from ..casing import snake_to_camel
from ..default_resolver import default_resolver
from .node_interface import NodeID, NodeInterface

DateTimeType = ScalarType(name="DateTime", serialize=str)  # pylint: disable=invalid-name

typemap = {
    types.Integer: Int,
    types.INTEGER: Int,
    types.Date: String,
    types.Time: String,
    types.String: String,
    types.Text: String,
    types.Unicode: String,
    types.UnicodeText: String,
    postgresql.UUID: String,
    postgresql.INET: String,
    postgresql.CIDR: String,
    types.DateTime: String,
}


if typing.TYPE_CHECKING:
    from nebulous.sql.table_base import TableBase


@lru_cache()
def convert_column(
    column, output_type: typing.Union[Field, InputField] = Field
) -> typing.Union[Field, InputField]:
    """Converts a sqlalchemy column into a graphql field or input field"""
    gql_type = typemap.get(type(column.type), String)
    notnull = not column.nullable
    return_type = NonNull(gql_type) if notnull and output_type == Field else gql_type

    # TODO(OR): clean up.
    if output_type == Field:
        return output_type(return_type, resolver=default_resolver)
    else:
        return output_type(return_type)



@lru_cache()
def convert_composite(composite) -> typing.Union[Field, InputField]:
    """Converts a sqlalchemy composite field into a graphql object type"""
    composite = composite
    raise NotImplementedError("Composite fields are not yet supported")


def relationship_is_nullable(relationship: RelationshipProperty, source: TableBase) -> bool:
    """Checks if a sqlalchemy orm relationship is nullable"""
    for local_col, remote_col in relationship.local_remote_pairs:
        if local_col.nullable or remote_col.nullable:
            return True
    return False


def relationship_to_attr_name(relationship: RelationshipProperty) -> str:
    """ """
    return (
        relationship.key
        + "By"
        + "And".join([snake_to_camel(col.name) for col in relationship.local_columns])
    )


@lru_cache()
def table_factory(sqla_model):
    name = snake_to_camel(sqla_model.__table__.name)

    def build_attrs():
        attrs = {}

        # Override id to relay standard
        attrs["nodeId"] = Field(NonNull(NodeID), resolver=default_resolver)

        for column in sqla_model.columns:
            key = column.name
            attrs[key] = convert_column(column)

            for relationship in sqla_model.relationships:
                direction = relationship.direction
                to_sqla_model = relationship.mapper.class_
                is_nullable = relationship_is_nullable(relationship, sqla_model)

                # Name of the attribute on the model
                attr_key = relationship_to_attr_name(relationship)

                # TODO(OR): Update so key is set by relevant fields
                # If this model has 1 counterpart, do not use a list
                if direction == interfaces.MANYTOONE:
                    _type = table_factory(to_sqla_model)
                    _type = NonNull(_type) if not is_nullable else _type
                    attrs[attr_key] = Field(_type, resolver=default_resolver)

                elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
                    from .connection import connection_factory, connection_args_factory

                    connection = connection_factory(to_sqla_model)
                    connection_args = connection_args_factory(to_sqla_model)
                    attrs[attr_key] = Field(
                        connection if is_nullable else NonNull(connection),
                        args=connection_args,
                        resolver=default_resolver,
                    )

        return attrs

    return_type = TableType(
        name=name, fields=build_attrs, interfaces=[NodeInterface], description=""
    )
    return_type.sqla_model = sqla_model

    return return_type


def encode(text_to_encode, encoding="base64"):
    return func.encode(cast(text_to_encode, BYTEA()), cast(encoding, sqlalchemy.Text()))


MODES = ["ONE", "NODES", "EDGES"]


def resolve_one(
    tree, parent_query: "cte", arguments: typing.Dict = None, result_wrapper=func.json_build_object
):
    """Resolves a single record from a table"""
    return_type = tree["return_type"]

    sqla_model = return_type.sqla_model

    query = parent_query if parent_query is not None else return_type.sqla_model.__table__.alias()

    # Maps graphql model attribute to sqla relationship
    relation_map = {relationship_to_attr_name(rel): rel for rel in sqla_model.relationships}

    fields = tree["fields"]

    # Always return the table name in each row
    builder = [literal("_table_name"), literal(sqla_model.__table__.name)]

    for tree_field in fields:
        field_name = tree_field["name"]
        field_alias = tree_field["alias"]

        # Handle basic attribute access case
        if hasattr(sqla_model, field_name):
            builder.extend([literal(field_alias), getattr(query.c, field_name)])

        # Handle NodeID case
        elif field_name == "nodeId":
            # Move this into node_interface
            builder.extend([literal(field_alias), resolve_node_id(query, sqla_model)])

        # Handle Relationships
        elif field_name in relation_map.keys():
            relation = relation_map[field_name]
            # Table we're joinig to
            joined_table = list(relation.remote_side)[0].table.alias()

            where_clause = []
            for local_col, remote_col in relation.local_remote_pairs:
                where_clause.extend(
                    [
                        getattr(parent_query.c, local_col.name)
                        == getattr(joined_table.c, remote_col.name)
                    ]
                )

            # Many to One relationship
            if relation.direction == interfaces.MANYTOONE:
                builder.extend(
                    [
                        literal(field_alias),
                        select([resolve_one(tree_field, parent_query=joined_table)])
                        .where(*where_clause)
                        .label("q"),
                    ]
                )

            # Many to One relationship
            elif relation.direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
                builder.extend(
                    [
                        literal(field_name),
                        select([resolve_connection(tree_field, parent_query=joined_table)])
                        .where(*where_clause)
                        .label("w"),
                    ]
                )
            else:
                raise NotImplementedError(f"Unknown relationship type {relation.direction}")

        else:
            # TODO(OR): This will have to be removed when end user extensibility feature is added
            raise NotImplementedError(f"Unknown field {relation.direction}")

    return result_wrapper(*builder)


def resolve_connection(tree, parent_query, arguments: typing.Dict = None):
    """Resolves a single record from a table"""

    query = parent_query
    fields = tree["fields"]

    # Always return the table name in each row
    builder = []

    for tree_field in fields:
        field_name = tree_field["name"]
        field_alias = tree_field["alias"]

        if field_name == "nodes":
            result_wrapper = lambda *x: func.json_agg(func.json_build_object(*x))
            builder.extend(
                [
                    literal(field_alias),
                    resolve_one(tree_field, query, result_wrapper=result_wrapper),
                ]
            )

        elif field_name == "edges":
            # result_wrapper = lambda *x: func.json_agg(func.json_build_object())

            edge_fields = tree_field["fields"]

            edge_field_map = {e["name"]: e for e in edge_fields}

            edge_node_field = edge_field_map.get("node")
            edge_cursor_field = edge_field_map.get("cursor")

            if edge_node_field and edge_cursor_field:
                edge_node_alias = edge_node_field["alias"]
                edge_cursor_alias = edge_cursor_field["alias"]

                builder.extend(
                    [
                        literal(field_alias),  # edges
                        func.array_agg(
                            func.json_build_object(
                                literal(edge_node_alias),  # nodes
                                # node query
                                resolve_one(
                                    edge_node_field, query, result_wrapper=func.json_build_object
                                ),
                                # (literal(cursor_alias), cursor)
                                literal(edge_cursor_alias),
                                resolve_cursor(query, tree["return_type"].sqla_model),
                            )
                        ),
                    ]
                )

        elif field_name == "pageInfo":
            print("Delegating for page info")

        elif field_name == "totalCount":
            builder.extend(
                [literal(field_alias), func.count(literal(1, type_=sqlalchemy.Integer()))]
            )
        else:
            raise NotImplementedError(f"Unreachable. No field {field_name} on connection")

    return func.json_build_object(*builder)


def resolve_node_id(query, sqla_model):
    return encode(
        literal(sqla_model.__table__.name) + literal(":") + cast(query.c.id, sqlalchemy.String())
    )


def resolve_cursor(query, sqla_model):
    return encode(
        literal(sqla_model.__table__.name)
        + literal(":cursor:")
        + cast(query.c.id, sqlalchemy.String())
    )
