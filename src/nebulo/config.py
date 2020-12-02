from inspect import isclass
from typing import Optional, Tuple, Type, Union

from nebulo.env import EnvManager
from nebulo.sql.inspect import get_comment, get_foreign_key_constraint_from_relationship, get_table_name, to_table
from nebulo.sql.reflection.function import SQLFunction
from nebulo.sql.reflection.views import ViewMixin
from nebulo.sql.table_base import TableProtocol
from nebulo.text_utils import snake_to_camel, to_plural
from parse import parse
from sqlalchemy import ForeignKeyConstraint, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql.schema import Column
from typing_extensions import Literal

ENV = EnvManager.get_environ()


class Config:

    CONNECTION = ENV.get("NEBULO_CONNECTION")
    SCHEMA = ENV.get("NEBULO_SCHEMA")
    JWT_IDENTIFIER = ENV.get("NEBULO_JWT_IDENTIFIER")
    JWT_SECRET = ENV.get("NEBULO_JWT_SECRET")
    DEFAULT_ROLE = ENV.get("NEBULO_DEFAULT_ROLE")

    @staticmethod
    def function_name_mapper(sql_function: SQLFunction) -> str:
        """to_upper -> toUpper"""
        return snake_to_camel(sql_function.name, upper=False)

    @staticmethod
    def function_type_name_mapper(sql_function: SQLFunction) -> str:
        """to_upper -> ToUpper"""
        return snake_to_camel(sql_function.name, upper=True)

    @classmethod
    def table_type_name_mapper(cls, sqla_table: TableProtocol) -> str:
        table_comment = get_comment(sqla_table)

        # If an @name directive exists, use it
        maybe_name: Optional[str] = cls.read_name_directive(table_comment)
        if maybe_name:
            return maybe_name

        table_name = get_table_name(sqla_table)
        return snake_to_camel(table_name)

    @classmethod
    def table_name_mapper(cls, sqla_table: TableProtocol) -> str:
        """Return the type name with the first character lower case"""
        type_name = cls.table_type_name_mapper(sqla_table)
        return type_name[0].lower() + type_name[1:]

    @classmethod
    def column_name_mapper(cls, column: Column) -> str:
        """Return the type name with the first character lower case"""
        column_comment = get_comment(column)

        # If an @name directive exists, use it
        maybe_name: Optional[str] = cls.read_name_directive(column_comment)
        if maybe_name:
            return maybe_name

        column_key = column.key
        type_name = snake_to_camel(column_key)
        return type_name[0].lower() + type_name[1:]

    @staticmethod
    def read_name_directive(comment: str) -> Optional[str]:
        """Returns the name following a @name comment directive"""
        lines = comment.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("@name"):
                line = line.lstrip("@name")
                name = line.strip()
                if name:
                    return name
        return None

    @staticmethod
    def enum_name_mapper(enum: Type[postgresql.base.ENUM]) -> str:
        return snake_to_camel((enum.name or "") + "_enum", upper=True)

    @staticmethod
    def read_foreign_key_comment_directive(comment: str) -> Tuple[Optional[str], Optional[str]]:
        """Accepts a comment from a foreign key backing a sqlalchemy RelationshipProperty and searches for
        a comment directive defining what the names for each side of the relationship should be for the local
        and remote graphql models on either side.

        Template:
            @name {local_name_for_remote} {remote_name_for_local}

        Example:
            Given:
                ALTER TABLE public.address
                ADD CONSTRAINT fk_address_to_person
                FOREIGN KEY (address_id)
                REFERENCES public.person (id);

            The comment

                COMMENT ON CONSTRAINT fk_address_to_person
                ON public.addresses
                IS E'@name Person Addresses';

            Would give:
                - The "Person" graphql model an "Addresses" field
                - The "Adress" graphql model a "Person" field
        """

        template = "@name {local_name_for_remote} {remote_name_for_local}"

        lines = comment.split("\n")
        for line in lines:
            line = line.strip()
            match = parse(template, line)
            if match is not None:
                local_name, remote_name = match.named.values()
                return (
                    local_name,
                    remote_name,
                )
        return None, None

    @classmethod
    def relationship_name_mapper(cls, relationship: RelationshipProperty) -> str:

        # Check the foreign key backing the relationship for a comment defining its name
        backing_fkey = get_foreign_key_constraint_from_relationship(relationship)
        if backing_fkey is not None:
            comment: str = get_comment(backing_fkey)
            local_name, remote_name = cls.read_foreign_key_comment_directive(comment)
            if local_name and remote_name:
                backing_fkey_parent_entity = backing_fkey.parent  # type: ignore
                fkey_parent_table: Table = to_table(backing_fkey_parent_entity)
                relationship_parent_table: Table = to_table(relationship.parent)
                if fkey_parent_table == relationship_parent_table:
                    return local_name
                return remote_name

        # No comment directive existed, reverting to default

        # Union of Mapper or ORM instance
        referred_cls = to_table(relationship.argument)
        # if hasattr(referred_cls, "class_"):
        #    referred_cls = referred_cls.class_
        # elif callable(referred_cls):
        #    referred_cls = referred_cls()

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
        entity: Union[TableProtocol, Column, ForeignKeyConstraint],
        operation: Union[
            Literal["read"],
            Literal["create"],
            Literal["update"],
            Literal["delete"],
            Literal["read_one"],
            Literal["read_all"],
        ],
    ) -> bool:
        """Shared SQL comment parsing logic for excludes"""
        comment: str = get_comment(entity)
        lines = comment.split("\n")
        for line in lines:
            if "@exclude" in line:
                operations_dirty = line[len("@exclude") :].split(",")
                operations_clean = {x.strip() for x in operations_dirty}
                if operation in operations_clean:
                    return True
        return False

    ###########
    # Exclude #
    ###########

    @classmethod
    def exclude_read(cls, entity: Union[TableProtocol, Column, ForeignKeyConstraint]) -> bool:
        """Should the entity be excluded from reads? e.g. entity(nodeId ...) and allEntities(...)"""
        return cls._exclude_check(entity, "read")

    @classmethod
    def exclude_read_one(cls, entity: Union[TableProtocol, Column]) -> bool:
        """Should the entity be excluded from reads? e.g. entity(nodeId ...)"""
        return any([cls._exclude_check(entity, "read_one"), cls.exclude_read(entity)])

    @classmethod
    def exclude_read_all(cls, entity: Union[TableProtocol, Column]) -> bool:
        """Should the entity be excluded from reads? e.g. allEntities(...)"""
        return any([cls._exclude_check(entity, "read_all"), cls.exclude_read(entity)])

    @classmethod
    def exclude_create(cls, entity: Union[TableProtocol, Column]) -> bool:
        """Should the entity be excluded from create mutations?"""
        # Views do not support insert
        if isclass(entity) and issubclass(entity, ViewMixin):  # type: ignore
            return True

        return cls._exclude_check(entity, "create")

    @classmethod
    def exclude_update(cls, entity: Union[TableProtocol, Column]) -> bool:
        """Should the entity be excluded from update mutations?"""

        # Views do not support updates
        if isclass(entity) and issubclass(entity, ViewMixin):  # type: ignore
            return True

        return cls._exclude_check(entity, "update")

    @classmethod
    def exclude_delete(cls, entity: Union[TableProtocol, Column]) -> bool:
        """Should the entity be excluded from delete mutations?"""

        # Views do not support deletes
        if isclass(entity) and issubclass(entity, ViewMixin):  # type: ignore
            return True

        return cls._exclude_check(entity, "delete")
