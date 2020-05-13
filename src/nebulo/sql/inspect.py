# pylint: disable=unsubscriptable-object, invalid-name
from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any, List

from nebulo.sql.table_base import TableBase
from sqlalchemy import Column
from sqlalchemy import inspect as sql_inspect
from sqlalchemy.orm import RelationshipProperty

if TYPE_CHECKING:
    RelationshipPropertyType = RelationshipProperty[Any]
    ColumnType = Column[Any]
else:
    RelationshipPropertyType = RelationshipProperty
    ColumnType = Column


@lru_cache()
def get_table_name(sqla_model: TableBase) -> str:
    """Name of the table"""
    return sqla_model.__table__.name


@lru_cache()
def get_relationships(sqla_model: TableBase) -> List[RelationshipPropertyType]:
    """Relationships with other tables"""
    return list(sql_inspect(sqla_model).relationships)


@lru_cache()
def get_primary_key_columns(sqla_model: TableBase) -> List[ColumnType]:
    """Primary key"""
    return [x for x in sqla_model.__table__.primary_key.columns]


@lru_cache()
def get_columns(sqla_model: TableBase) -> List[ColumnType]:
    """Columns on the table"""
    return [x for x in sqla_model.__table__.columns]


@lru_cache()
def is_nullable(relationship: RelationshipProperty) -> bool:
    """Checks if a sqlalchemy orm relationship is nullable"""
    for local_col, remote_col in relationship.local_remote_pairs:
        if local_col.nullable or remote_col.nullable:
            return True
    return False
