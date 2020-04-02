# pylint: disable=invalid-name
from __future__ import annotations

import typing
from functools import lru_cache

import sqlalchemy
from sqlalchemy import cast, func, types
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import RelationshipProperty
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
    pass


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


def resolve_one_to_relationship(obj, info, relationship_key=None, **kwargs):
    return getattr(obj, relationship_key)


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

        return attrs

    return_type = TableType(
        name=name, fields=build_attrs, interfaces=[NodeInterface], description=""
    )
    return_type.sqla_model = sqla_model

    return return_type


def encode(text_to_encode, encoding="base64"):
    return func.encode(cast(text_to_encode, BYTEA()), cast(encoding, sqlalchemy.Text()))


def resolve_one(tree, parent_query: "cte"):
    return_type = tree["return_type"]
    sqla_model = return_type.sqla_model

    query = parent_query if parent_query is not None else return_type.sqla_model.__table__.alias()

    fields = tree["fields"]

    builder = []
    for tree_field in fields:
        field_name = tree_field["name"]
        field_alias = tree_field["alias"]
        # no args accepted
        # subfields possible
        if hasattr(sqla_model, field_name):
            builder.extend([literal(field_alias), getattr(query.c, field_name)])
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
            )  # sql_encode(query.c.id)])
        else:
            print("Field named:", field_name, "not known")

    return func.json_build_object(*builder)
