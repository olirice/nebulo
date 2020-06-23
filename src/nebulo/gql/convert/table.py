# pylint: disable=invalid-name,unsubscriptable-object
from __future__ import annotations

from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import Argument, Field, NonNull, TableType
from nebulo.gql.convert.column import convert_column
from nebulo.gql.relay.node_interface import ID, NodeInterface
from nebulo.gql.resolve.resolvers.default import default_resolver
from nebulo.sql.inspect import get_columns, get_relationships, is_nullable
from nebulo.sql.table_base import TableProtocol
from sqlalchemy.orm import interfaces


def table_field_factory(sqla_model: TableProtocol, resolver) -> Field:
    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    node = table_factory(sqla_model)
    return Field(
        node,
        args={"nodeId": Argument(NonNull(ID))},
        resolve=resolver,
        description=f"Reads a single {relevant_type_name} using its globally unique ID",
    )


@lru_cache()
def table_factory(sqla_model: TableProtocol) -> TableType:
    """
    Reflects a SQLAlchemy table into a graphql-core GraphQLObjectType

    Parameters
    ----------
    sqla_model
        A SQLAlchemy ORM Table

    """
    from .connection import connection_field_factory

    name = Config.table_type_name_mapper(sqla_model)

    def build_attrs():
        attrs = {}

        # Override id to relay standard
        attrs["nodeId"] = Field(NonNull(ID), resolve=default_resolver)

        for column in get_columns(sqla_model):
            if not Config.exclude_read(column):
                key = Config.column_name_mapper(column)
                attrs[key] = convert_column(column)

        for relationship in get_relationships(sqla_model):
            direction = relationship.direction
            to_sqla_model = relationship.mapper.class_
            relationship_is_nullable = is_nullable(relationship)

            # Name of the attribute on the model
            attr_key = Config.relationship_name_mapper(relationship)

            # If this model has 1 counterpart, do not use a list
            if direction == interfaces.MANYTOONE:
                _type = table_factory(to_sqla_model)
                _type = NonNull(_type) if not relationship_is_nullable else _type
                attrs[attr_key] = Field(_type, resolve=default_resolver)

            # Otherwise, set it up as a connection
            elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
                connection_field = connection_field_factory(
                    to_sqla_model, resolver=default_resolver, not_null=relationship_is_nullable
                )
                attrs[attr_key] = connection_field

        return attrs

    return_type = TableType(
        name=name, fields=build_attrs, interfaces=[NodeInterface], description="", sqla_model=sqla_model
    )

    return return_type
