# pylint: disable=invalid-name
from __future__ import annotations

import typing
from functools import lru_cache, partial

from sqlalchemy import types
from sqlalchemy.dialects import postgresql
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
)
from ..casing import snake_to_camel
from .base import TableToGraphQLField
from .node import NodeID, NodeInterface

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
    gql_type = String if column.name != "id" else typemap[type(column.type)]
    notnull = not (column.nullable or False)
    return_type = NonNull(gql_type) if notnull else gql_type
    return output_type(return_type)


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
    print(info.path, info.return_type, "\n\t", obj, "\n\t", kwargs)
    return getattr(obj, relationship_key)


class Table(TableToGraphQLField):
    @property
    def type_name(self):
        return snake_to_camel(self.sqla_model.__table__.name)

    @property
    def _type(self):
        from .connection import Connection

        node_id = NodeID(self.sqla_model)
        self.relationship_key = None

        def build_attrs():
            attrs = {}

            # Override id to relay standard
            attrs["nodeId"] = node_id.field(nullable=False)

            for column in self.sqla_model.columns:
                attrs[column.name] = convert_column(column)

            for relationship in self.sqla_model.relationships:
                direction = relationship.direction
                to_sqla_model = relationship.mapper.class_
                is_nullable = relationship_is_nullable(relationship)

                # Name of the attribute on the model
                attr_key = relationship_to_attr_name(relationship)

                resolver = partial(resolve_one_to_relationship, relationship_key=relationship.key)

                # TODO(OR): Update so key is set by relevant fields
                # If this model has 1 counterpart, do not use a list
                if direction == interfaces.MANYTOONE:
                    _type = Table(to_sqla_model).type
                    _type = NonNull(_type) if not is_nullable else _type
                    attrs[attr_key] = Field(_type, resolver=resolver)

                elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
                    model_connection = Connection(to_sqla_model)
                    attrs[attr_key] = model_connection.field(nullable=is_nullable)

            return attrs

        return ObjectType(
            name=self.type_name, fields=build_attrs, interfaces=[NodeInterface], description=""
        )

    def resolver(self, obj, info: ResolveInfo, **user_kwargs):
        print(info.path, info.return_type, "\n\t", obj, "\n\t", user_kwargs)
        sqla_model = self.sqla_model
        context = info.context
        session = context["session"]
        return_type = info.return_type

        if "nodeId" in user_kwargs:
            # TODO(OR) validate nodeId is correct type
            return session.query(sqla_model).first()

        # If not those 2 conditions, skip and delegate
        # Resolving nodes
        if user_kwargs:
            return session.query(sqla_model).limit(user_kwargs["limit"]).all()

        return session.query(sqla_model).all()
