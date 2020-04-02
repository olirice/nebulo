"""
A base class to derive sql tables from
"""

from typing import Any, Dict, List, Tuple, Callable, Union, Optional
from inspect import Parameter, Signature

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.schema import Constraint, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy import Column, DateTime, func, inspect as sql_inspect
from sqlalchemy_utils import generic_repr

from .base import Base
from .utils import classproperty
from csql.sql.gql_base_mixin import GQLBaseMixin


@generic_repr
class TableBase(GQLBaseMixin, Base):
    """Base class for application sql tables"""

    __abstract__ = True
    __table_args__: Tuple[Any, Any] = ()
    __mapper_args__: Dict[str, Any] = {}

    @classproperty
    def table_name(cls) -> str:
        """Name of the table"""
        return cls.__table__.name

    @classproperty
    def columns(cls) -> List[Column]:
        """All columns in table"""
        return list(cls.__table__.columns)

    @classproperty
    def constraints(cls) -> List[Constraint]:
        """All constraints on the table"""
        return sorted(cls.__table__.constraints, key=lambda x: x.__class__.__name__ + x.name)

    @classproperty
    def unique_constraints(cls) -> List[UniqueConstraint]:
        """Unique constraints in the table"""
        return [x for x in cls.constraints if isinstance(x, UniqueConstraint)]

    @classproperty
    def primary_key(cls) -> Optional[PrimaryKeyConstraint]:
        """Primary key for the table"""
        maybe_empty_pkey = [x for x in cls.constraints if isinstance(x, PrimaryKeyConstraint)]
        return maybe_empty_pkey[0] if maybe_empty_pkey else None

    @classproperty
    def relationships(cls) -> List[RelationshipProperty]:
        """Relationships with other tables"""
        return list(sql_inspect(cls).relationships)
