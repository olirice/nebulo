# pylint: disable=invalid-name,unsubscriptable-object
from __future__ import annotations

import typing
from functools import lru_cache

from nebulo.gql.alias import Field, InputField, NonNull, String, TableType
from nebulo.gql.convert.node_interface import NodeID, NodeInterface
from nebulo.gql.convert.typemap import Typemap
from nebulo.gql.default_resolver import default_resolver
from nebulo.sql.inspect import get_columns, get_relationships, get_table_name
from nebulo.text_utils import snake_to_camel
from sqlalchemy.orm import RelationshipProperty, interfaces
from sqlalchemy.sql.schema import Column

if typing.TYPE_CHECKING:
    from nebulo.sql.table_base import TableBase

    ColumnType = Column[typing.Any]
    RelationshipPropertyType = RelationshipProperty[typing.Any]
else:
    ColumnType = Column
    RelationshipPropertyType = RelationshipProperty


@lru_cache()
def convert_column(
    column: ColumnType, output_type: typing.Union[Field, InputField] = Field
) -> typing.Union[Field, InputField]:
    """Converts a sqlalchemy column into a graphql field or input field"""
    gql_type = Typemap.get(type(column.type), String)
    notnull = not column.nullable
    return_type = NonNull(gql_type) if notnull and output_type == Field else gql_type

    # TODO(OR): clean up.
    if output_type == Field:
        return output_type(return_type, resolver=default_resolver)
    else:
        return output_type(return_type)


@lru_cache()
def relationship_is_nullable(relationship: RelationshipPropertyType, source: TableBase) -> bool:
    """Checks if a sqlalchemy orm relationship is nullable"""
    for local_col, remote_col in relationship.local_remote_pairs:
        if local_col.nullable or remote_col.nullable:
            return True
    return False


@lru_cache()
def relationship_to_attr_name(relationship: RelationshipPropertyType) -> str:
    """Collect the  """
    return relationship.key


@lru_cache()
def table_factory(sqla_model):
    name = snake_to_camel(get_table_name(sqla_model))

    def build_attrs():
        attrs = {}

        # Override id to relay standard
        attrs["nodeId"] = Field(NonNull(NodeID), resolver=default_resolver)

        for column in get_columns(sqla_model):
            key = column.key
            attrs[key] = convert_column(column)

        for relationship in get_relationships(sqla_model):
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
                    connection if is_nullable else NonNull(connection), args=connection_args, resolver=default_resolver
                )

        return attrs

    return_type = TableType(name=name, fields=build_attrs, interfaces=[NodeInterface], description="")
    return_type.sqla_model = sqla_model

    return return_type
