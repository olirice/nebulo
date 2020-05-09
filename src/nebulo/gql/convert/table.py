# pylint: disable=invalid-name,unsubscriptable-object
from __future__ import annotations

import typing
from functools import lru_cache

from nebulo.gql.alias import Field, NonNull, TableType
from nebulo.gql.convert.column import convert_column
from nebulo.gql.convert.factory_config import FactoryConfig
from nebulo.gql.convert.node_interface import NodeID, NodeInterface
from nebulo.gql.default_resolver import default_resolver
from nebulo.sql.inspect import get_columns, get_relationships
from nebulo.sql.table_base import TableBase
from sqlalchemy.orm import RelationshipProperty, interfaces
from sqlalchemy.sql.schema import Column

TableNameMapper = typing.Callable[[TableBase], str]
ColumnNameMapper = typing.Callable[[Column], str]
RelationshipNameMapper = typing.Callable[[RelationshipProperty], str]


def relationship_is_nullable(relationship: RelationshipProperty, source: TableBase) -> bool:
    """Checks if a sqlalchemy orm relationship is nullable"""
    for local_col, remote_col in relationship.local_remote_pairs:
        if local_col.nullable or remote_col.nullable:
            return True
    return False


@lru_cache()
def table_factory(sqla_model: TableBase) -> TableType:

    name = FactoryConfig.table_name_mapper(sqla_model)

    def build_attrs():
        attrs = {}

        # Override id to relay standard
        attrs["nodeId"] = Field(NonNull(NodeID), resolve=default_resolver)

        for column in get_columns(sqla_model):
            key = FactoryConfig.column_name_mapper(column)
            attrs[key] = convert_column(column)

        for relationship in get_relationships(sqla_model):
            direction = relationship.direction
            to_sqla_model = relationship.mapper.class_
            is_nullable = relationship_is_nullable(relationship, sqla_model)

            # Name of the attribute on the model
            attr_key = FactoryConfig.relationship_name_mapper(relationship)

            # TODO(OR): Update so key is set by relevant fields
            # If this model has 1 counterpart, do not use a list
            if direction == interfaces.MANYTOONE:
                _type = table_factory(to_sqla_model)
                _type = NonNull(_type) if not is_nullable else _type
                attrs[attr_key] = Field(_type, resolve=default_resolver)

            elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
                from .connection import connection_factory, connection_args_factory

                connection = connection_factory(to_sqla_model)
                connection_args = connection_args_factory(to_sqla_model)
                attrs[attr_key] = Field(
                    connection if is_nullable else NonNull(connection), args=connection_args, resolve=default_resolver
                )

        return attrs

    return_type = TableType(name=name, fields=build_attrs, interfaces=[NodeInterface], description="")
    return_type.sqla_model = sqla_model

    return return_type
