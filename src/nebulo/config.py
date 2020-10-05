from inspect import isclass
from typing import Union

from nebulo.env import EnvManager
from nebulo.sql.inspect import get_comment, get_table_name
from nebulo.sql.reflection.function import SQLFunction
from nebulo.sql.reflection.views import ViewMixin
from nebulo.sql.table_base import TableProtocol
from nebulo.text_utils import snake_to_camel, to_plural
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql.schema import Column
from typing_extensions import Literal

ENV = EnvManager.get_environ()


class Config:

    CONNECTION = ENV.get("NEBULO_CONNECTION")
    SCHEMA = ENV.get("NEBULO_SCHEMA")
    JWT_IDENTIFIER = ENV.get("NEBULO_JWT_IDENTIFIER")
    JWT_SECRET = ENV.get("NEBULO_JWT_SECRET")

    @staticmethod
    def function_name_mapper(sql_function: SQLFunction) -> str:
        """to_upper -> toUpper"""
        return snake_to_camel(sql_function.name, upper=False)

    @staticmethod
    def function_type_name_mapper(sql_function: SQLFunction) -> str:
        """to_upper -> ToUpper"""
        return snake_to_camel(sql_function.name, upper=True)

    @staticmethod
    def table_type_name_mapper(sqla_table: TableProtocol) -> str:
        table_name = get_table_name(sqla_table)
        return snake_to_camel(table_name)

    @classmethod
    def table_name_mapper(cls, sqla_table: TableProtocol) -> str:
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

    # SQL Comment Config
    @staticmethod
    def _exclude_check(
        entity: Union[TableProtocol, Column],
        operation: Union[Literal["read"], Literal["insert"], Literal["update"], Literal["delete"]],
    ) -> bool:
        """Shared SQL comment parsing logic for excludes"""
        comment: str = get_comment(entity)
        lines = comment.split("\n")
        for line in lines:
            if "@exclude" in line and operation in line:
                return True
        return False

    @classmethod
    def exclude_read(cls, entity: Union[TableProtocol, Column]) -> bool:
        """Should the entity be excluded from reads?"""
        return cls._exclude_check(entity, "read")

    @classmethod
    def exclude_insert(cls, entity: Union[TableProtocol, Column]) -> bool:
        """Should the entity be excluded from inserts?"""
        # Views do not support insert
        if isclass(entity) and issubclass(entity, ViewMixin):  # type: ignore
            return True

        return cls._exclude_check(entity, "insert")

    @classmethod
    def exclude_update(cls, entity: Union[TableProtocol, Column]) -> bool:
        """Should the entity be excluded from updates?"""

        # Views do not support updates
        if isclass(entity) and issubclass(entity, ViewMixin):  # type: ignore
            return True

        return cls._exclude_check(entity, "update")

    @classmethod
    def exclude_delete(cls, entity: Union[TableProtocol, Column]) -> bool:
        """Should the entity be excluded from deletes?"""

        # Views do not support deletes
        if isclass(entity) and issubclass(entity, ViewMixin):  # type: ignore
            return True

        return cls._exclude_check(entity, "delete")
