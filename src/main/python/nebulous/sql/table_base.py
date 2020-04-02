"""
A base class to derive sql tables from
"""

import datetime
from decimal import Decimal
from typing import Any, Dict, List, NoReturn, Optional, Tuple

from sqlalchemy import event
from sqlalchemy import inspect as sql_inspect
from sqlalchemy.orm import ColumnProperty, RelationshipProperty, mapper
from sqlalchemy.sql.schema import Constraint, PrimaryKeyConstraint, UniqueConstraint

from .base import Base
from .utils import classproperty

# from sqlalchemy_utils import generic_repr


# from nebulous.sql.gql_base_mixin import GQLBaseMixin


# @generic_repr
# class TableBase(GQLBaseMixin, ComputedColumnsMixin, OmitMixin, Base):
class TableBase(Base):
    """Base class for application sql tables"""

    __abstract__ = True
    __table_args__: Tuple[Any, Any] = ()
    __mapper_args__: Dict[str, Any] = {}

    @classproperty
    def table_name(cls) -> str:  # pylint: disable=no-self-argument
        """Name of the table"""
        return cls.__table__.name

    @classproperty
    def columns(cls) -> List[ColumnProperty]:  # pylint: disable=no-self-argument
        """All columns in table"""
        # return list(sql_inspect(cls).column_attrs.values())
        return list(cls.__table__.columns)

    @classproperty
    def constraints(cls) -> List[Constraint]:  # pylint: disable=no-self-argument
        """All constraints on the table"""
        return sorted(cls.__table__.constraints, key=lambda x: str(x))

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

    def to_dict(self):
        """Return the resource as a dictionary.
        """
        result_dict = {}
        for column in self.__table__.columns.keys():  # pylint: disable=no-member
            value = result_dict[column] = getattr(self, column, None)
            if isinstance(value, Decimal):
                result_dict[column] = float(result_dict[column])
            elif isinstance(value, datetime.datetime):
                result_dict[column] = value.isoformat()
        return result_dict


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


# @event.listens_for(Engine, "connect")
def set_sqlite_pragmas(dbapi_connection, connection_record):
    print("Setting pragmas")
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA TEMP_STORE=MEMORY")
    cursor.execute("PRAGMA JOURNAL_MODE=MEMORY")
    cursor.execute("PRAGMA SYNCHRONOUS=FULL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
