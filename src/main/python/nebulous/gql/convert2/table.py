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
    return output_type(return_type, resolver=default_resolver)


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

    node_id = NodeID

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

                    connection = connection_factory(sqla_model)
                    connection_args = connection_args_factory(sqla_model)
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


def resolve_one(tree, parent_query: "cte", mode="ONE"):  # , filters: typing.Dict[str, typing.Any]):
    """Resolves a single record from a table"""
    return_type = tree["return_type"]
    sqla_model = return_type.sqla_model

    query = parent_query if parent_query is not None else return_type.sqla_model.__table__.alias()

    # Maps graphql model attribute to sqla relationship
    to_one_relation_map = {
        relationship_to_attr_name(rel): rel
        for rel in sqla_model.relationships
        if rel.direction == interfaces.MANYTOONE
    }

    to_many_relation_map = {
        relationship_to_attr_name(rel): rel
        for rel in sqla_model.relationships
        if rel.direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY)
    }

    fields = tree["fields"]

    builder = []
    for tree_field in fields:
        field_name = tree_field["name"]
        field_alias = tree_field["alias"]

        # Handle basic attribute access case
        if hasattr(sqla_model, field_name):
            builder.extend([literal(field_alias), getattr(query.c, field_name)])

        # Handle NodeID case
        elif field_name == "nodeId":
            # Move this into node_interface
            builder.extend(
                [
                    literal(field_alias),
                    encode(
                        literal(sqla_model.__table__.name)
                        + literal(":")
                        + cast(query.c.id, sqlalchemy.String())
                    ),
                ]
            )
        # Handle ManyToOne relationships
        elif field_name in to_one_relation_map.keys():
            relation = to_one_relation_map[field_name]
            # Table we're joinig to
            joined_table = list(relation.remote_side)[0].table

            # Apply join as filters
            where_clause = relation_to_where_clause(
                left_query=parent_query,
                right_query=joined_table,
                left_tab_name=sqla_model.__table__.name,
                right_tab_name=joined_table.name,
                relation=relation,
            )

            builder.extend(
                [
                    literal(field_name),
                    select([resolve_one(tree_field, parent_query=joined_table)])
                    .where(*where_clause)
                    .label("q"),
                ]
            )

            # Handle ToMany relationships
            """
            Notes:
            
            Need a separate resolver for connections that delegates back to 
            resolve_one

            also need to move node_id resolver, and pageinfo resolver on their own.
            """

        elif field_name in to_many_relation_map.keys():
            relation = to_many_relation_map[field_name]
            # Table we're joinig to
            joined_table = list(relation.remote_side)[0].table

            # Apply join as filters
            where_clause = relation_to_where_clause(
                left_query=parent_query,
                right_query=joined_table,
                left_tab_name=sqla_model.__table__.name,
                right_tab_name=joined_table.name,
                relation=relation,
            )

            builder.extend(
                [
                    literal(field_name),
                    select([resolve_one(tree_field, parent_query=joined_table, mode="MANY")])
                    .where(*where_clause)
                    .label("q"),
                ]
            )

        else:
            print("Field named:", field_name, "not known")

    return (
        func.json_build_object(*builder)
        if mode == "ONE"
        else func.to_json(func.array_agg(func.json_build_object(*builder)))
    )


def relation_to_where_clause(
    left_query, right_query, left_tab_name: str, right_tab_name: str, relation
) -> "FilteredQuery":
    """

    """
    local_columns = list(relation.local_columns)

    # This only allows each column to be used for 1 foreign key
    remote_columns = [list(x.foreign_keys)[0].column for x in local_columns]

    if local_columns[0].table.name == left_tab_name:
        left_columns = local_columns
        right_columns = remote_columns
    else:
        left_columns = remote_columns
        right_columns = local_columns

    left_names = [x.name for x in left_columns]
    right_names = [x.name for x in right_columns]

    return [
        getattr(left_query.c, left_name) == getattr(right_query.c, right_name)
        for left_name, right_name in zip(left_names, right_names)
    ]
