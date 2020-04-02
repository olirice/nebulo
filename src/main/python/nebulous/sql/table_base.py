"""
A base class to derive sql tables from
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import MetaData
from sqlalchemy import inspect as sql_inspect
from sqlalchemy import tuple_
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import ColumnProperty, RelationshipProperty
from sqlalchemy.sql.schema import Constraint, PrimaryKeyConstraint, UniqueConstraint

from nebulous.sql.computed_column_mixin import ComputedColumnsMixin

from .utils import classproperty


def build_base():
    return automap_base(metadata=MetaData())


class TableBase(build_base(), ComputedColumnsMixin):
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

    @hybrid_property
    def cursor(self) -> "SQLExpression":
        return tuple_(*self.primary_key.columns)
