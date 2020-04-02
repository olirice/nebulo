"""
A base class to derive sql tables from
"""

from typing import Any, Dict, List, NoReturn, Optional, Tuple

from sqlalchemy import Column, event
from sqlalchemy import inspect as sql_inspect
from sqlalchemy.orm import mapper
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.schema import Constraint, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy_utils import generic_repr

from csql.sql.computed_column_mixin import ComputedColumnsMixin
from csql.sql.ddl_mixin import OmitMixin
from csql.sql.gql_base_mixin import GQLBaseMixin

from .base import Base
from .utils import classproperty


@generic_repr
class TableBase(GQLBaseMixin, ComputedColumnsMixin, OmitMixin, Base):
    """Base class for application sql tables"""

    __abstract__ = True
    __table_args__: Tuple[Any, Any] = ()
    __mapper_args__: Dict[str, Any] = {}

    @classproperty
    def table_name(cls) -> str:  # pylint: disable=no-self-argument
        """Name of the table"""
        return cls.__table__.name

    @classproperty
    def columns(cls) -> List[Column]:  # pylint: disable=no-self-argument
        """All columns in table"""
        return list(cls.__table__.columns)

    @classproperty
    def constraints(cls) -> List[Constraint]:  # pylint: disable=no-self-argument
        """All constraints on the table"""
        return sorted(cls.__table__.constraints, key=lambda x: x.__class__.__name__ + x.name)

    @classproperty
    def unique_constraints(cls) -> List[UniqueConstraint]:  # pylint: disable=no-self-argument
        """Unique constraints in the table"""
        return [x for x in cls.constraints if isinstance(x, UniqueConstraint)]

    @classproperty
    def primary_key(cls) -> Optional[PrimaryKeyConstraint]:  # pylint: disable=no-self-argument
        """Primary key for the table"""
        maybe_empty_pkey = [x for x in cls.constraints if isinstance(x, PrimaryKeyConstraint)]
        return maybe_empty_pkey[0] if maybe_empty_pkey else None

    @classproperty
    def relationships(cls) -> List[RelationshipProperty]:  # pylint: disable=no-self-argument
        """Relationships with other tables"""
        return list(sql_inspect(cls).relationships)

    def update(self, **kwargs: Dict[str, Any]) -> NoReturn:
        """Updates the row instance in place by replacing column existing values with thos provided
        in the kwarg dict. The dict's keys match the model's attributes/columns. Incorrect or
        unknown keys result in an Exception"""
        column_names = {x.name for x in self.columns}
        for key, value in kwargs.items():
            if key in column_names:
                setattr(self, key, value)
            else:
                raise KeyError(f"Key {key} does not exist on model {self.table_name}")

    computed_columns = []


@event.listens_for(mapper, "before_configured", once=True)
def before_tooling_application():
    """This is a bad idea"""
    pass  # pylint: disable=unnecessary-pass


@event.listens_for(mapper, "after_configured", once=True)
def after_tooling_application():
    """Hooks for post-mapper config"""
    tables = [x for x in TableBase.__subclasses__()]

    for table in tables:
        for column in table.columns:
            comment: str = column.comment or ""  # pylint: disable=unused-variable
            comment
            # if "@ommit" in comment:
            #    delattr(table, column.name)
            #    print(f"Omitted {column.name}")
