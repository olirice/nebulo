from nebulo.env import EnvManager
from nebulo.sql.inspect import get_table_name
from nebulo.sql.reflection.function import SQLFunction
from nebulo.sql.table_base import TableBase
from nebulo.text_utils import snake_to_camel, to_plural
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql.schema import Column

ENV = EnvManager.get_environ()


class Config:
    @staticmethod
    def function_name_mapper(sql_function: SQLFunction) -> str:
        """to_upper -> toUpper"""
        return snake_to_camel(sql_function.name, upper=False)

    @staticmethod
    def function_type_name_mapper(sql_function: SQLFunction) -> str:
        """to_upper -> ToUpper"""
        return snake_to_camel(sql_function.name, upper=True)

    @staticmethod
    def table_type_name_mapper(sqla_table: TableBase) -> str:
        table_name = get_table_name(sqla_table)
        return snake_to_camel(table_name)

    @classmethod
    def table_name_mapper(cls, sqla_table: TableBase) -> str:
        """Return the type name with the first character lower case"""
        type_name = cls.table_type_name_mapper(sqla_table)
        return type_name[0].lower() + type_name[1:]

    @staticmethod
    def column_name_mapper(column: Column) -> str:
        return snake_to_camel(column.name, upper=False)

    @staticmethod
    def relationship_name_mapper(relationship: RelationshipProperty) -> str:
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

    CONNECTION = ENV.get("NEBULO_CONNECTION")
    SCHEMA = ENV.get("NEBULO_SCHEMA")
    JWT_IDENTIFIER = ENV.get("NEBULO_JWT_IDENTIFIER")
    JWT_SECRET = ENV.get("NEBULO_JWT_SECRET")
