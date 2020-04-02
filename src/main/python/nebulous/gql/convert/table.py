# pylint: disable=invalid-name
from __future__ import annotations

import typing
from functools import lru_cache

import sqlalchemy
from sqlalchemy import cast, func, types
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import RelationshipProperty, interfaces

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


@lru_cache()
def relationship_is_nullable(relationship: RelationshipProperty, source: TableBase) -> bool:
    """Checks if a sqlalchemy orm relationship is nullable"""
    for local_col, remote_col in relationship.local_remote_pairs:
        if local_col.nullable or remote_col.nullable:
            return True
    return False


@lru_cache()
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