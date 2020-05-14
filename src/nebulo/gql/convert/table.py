# pylint: disable=invalid-name,unsubscriptable-object
from __future__ import annotations

from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import Field, NonNull, TableType
from nebulo.gql.convert.column import convert_column
from nebulo.gql.convert.node_interface import NodeID, NodeInterface
from nebulo.gql.resolver.default import default_resolver
from nebulo.sql.inspect import get_columns, get_relationships, is_nullable
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import interfaces


@lru_cache()
def table_factory(sqla_model: DeclarativeMeta) -> TableType:
    """
    Reflects a SQLAlchemy table into a graphql-core GraphQLObjectType

    Parameters
    ----------
    sqla_model
        A SQLAlchemy ORM Table

    """
    from .connection import connection_factory, connection_args_factory

    name = Config.table_name_mapper(sqla_model)

    def build_attrs():
        attrs = {}

        # Override id to relay standard
        attrs["nodeId"] = Field(NonNull(NodeID), resolve=default_resolver)

        for column in get_columns(sqla_model):
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

                connection = connection_factory(to_sqla_model)
                connection_args = connection_args_factory(to_sqla_model)
                attrs[attr_key] = Field(
                    connection if relationship_is_nullable else NonNull(connection),
                    args=connection_args,
                    resolve=default_resolver,
                )

        return attrs

    return_type = TableType(
        name=name, fields=build_attrs, interfaces=[NodeInterface], description="", sqla_model=sqla_model
    )

    return return_type
