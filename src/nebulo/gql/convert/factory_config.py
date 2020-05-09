import typing

from nebulo.sql.inspect import get_table_name
from nebulo.sql.table_base import TableBase
from nebulo.text_utils import snake_to_camel, to_plural
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql.schema import Column


def default_table_name_mapper(sqla_table: TableBase) -> str:
    table_name = get_table_name(sqla_table)
    return snake_to_camel(table_name)


def default_column_name_mapper(column: Column) -> str:
    return snake_to_camel(column.name, upper=False)


def default_relationship_name_mapper(relationship: RelationshipProperty) -> str:
    # Union of Mapper or ORM instance
    referred_cls = relationship.argument
    if hasattr(referred_cls, "class_"):
        referred_cls = referred_cls.class_

    referred_name = get_table_name(referred_cls)
    cardinal_name = to_plural(referred_name) if relationship.uselist else referred_name
    camel_name = snake_to_camel(cardinal_name, upper=False)
    relationship_name = (
        camel_name
        + "By"
        + "And".join(
            snake_to_camel(local_col.name, upper=True) + "To" + snake_to_camel(remote_col.name, upper=True)
            for local_col, remote_col in relationship.local_remote_pairs
        )
    )
    return relationship_name


TableNameMapper = typing.Callable[[TableBase], str]
ColumnNameMapper = typing.Callable[[Column], str]
RelationshipNameMapper = typing.Callable[[RelationshipProperty], str]


class FactoryConfig:
    table_name_mapper: TableNameMapper = default_table_name_mapper
    column_name_mapper: ColumnNameMapper = default_column_name_mapper
    relationship_name_mapper: RelationshipNameMapper = default_relationship_name_mapper
