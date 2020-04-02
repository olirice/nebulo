from functools import lru_cache
from typing import List

from nebulous.sql.table_base import TableBase
from sqlalchemy import inspect as sql_inspect
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql.schema import PrimaryKeyConstraint, UniqueConstraint


@lru_cache()
def get_table_name(sqla_model: TableBase) -> str:
    """Name of the table"""
    return sqla_model.__table__.name


@lru_cache()
def get_unique_constraints(sqla_model: TableBase) -> List[UniqueConstraint]:
    """Unique constraints in the table"""
    return [x for x in sqla_model.constraints if isinstance(x, UniqueConstraint)]


@lru_cache()
def get_relationships(sqla_model: TableBase) -> List[RelationshipProperty]:
    """Relationships with other tables"""
    return list(sql_inspect(sqla_model).relationships)


@lru_cache()
def get_primary_key(sqla_model: TableBase) -> List[PrimaryKeyConstraint]:
    """Primary key"""
    return sqla_model.__table__.primary_key
