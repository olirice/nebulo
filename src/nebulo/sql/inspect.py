# pylint: disable=unsubscriptable-object, invalid-name
from __future__ import annotations

from functools import lru_cache
from typing import List, Union

from nebulo.sql.table_base import TableProtocol
from sqlalchemy import Column, Table
from sqlalchemy import inspect as sql_inspect
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql.schema import Constraint


@lru_cache()
def get_table_name(entity: Union[Table, TableProtocol]) -> str:
    """Name of the table"""
    return str(to_table(entity).name)


@lru_cache()
def get_relationships(sqla_model: TableProtocol) -> List[RelationshipProperty]:
    """Relationships with other tables"""
    return list(sql_inspect(sqla_model).relationships)


@lru_cache()
def get_primary_key_columns(sqla_model: TableProtocol) -> List[Column]:
    """Primary key"""
    return [x for x in sqla_model.__table__.primary_key.columns]


@lru_cache()
def get_columns(sqla_model: TableProtocol) -> List[Column]:
    """Columns on the table"""
    return [x for x in sqla_model.__table__.columns]


@lru_cache()
def get_constraints(entity: Union[TableProtocol, Table]) -> List[Constraint]:
    """Retrieve constraints from a table"""
    return list(to_table(entity).constraints)


@lru_cache()
def is_nullable(relationship: RelationshipProperty) -> bool:
    """Checks if a sqlalchemy orm relationship is nullable"""
    for local_col, remote_col in relationship.local_remote_pairs:
        if local_col.nullable or remote_col.nullable:
            return True
    return False


def to_table(entity: Union[Table, TableProtocol]) -> Table:
    """Coerces Table and ORM Table to Table"""
    if isinstance(entity, Table):
        return entity
    return entity.__table__


def get_comment(entity: Union[Table, TableProtocol, Column, Constraint]) -> str:
    """Get comment on entity"""
    if isinstance(entity, TableProtocol):
        return to_table(entity).comment or ""
    elif isinstance(entity, Table):
        return entity.comment or ""
    elif isinstance(entity, Column):
        return entity.comment or ""
    elif isinstance(entity, Constraint):
        if hasattr(entity, "info"):
            return getattr(entity, "info").get("comment") or ""
        return ""
    raise ValueError("invalid entity passed to get_comment")
