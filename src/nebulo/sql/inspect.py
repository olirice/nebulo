# pylint: disable=unsubscriptable-object, invalid-name
from __future__ import annotations

from functools import lru_cache, singledispatch
from typing import List, Union

from nebulo.sql.table_base import TableProtocol
from sqlalchemy import Column
from sqlalchemy import inspect as sql_inspect
from sqlalchemy.orm import RelationshipProperty


@lru_cache()
def get_table_name(sqla_model: TableProtocol) -> str:
    """Name of the table"""
    return str(sqla_model.__table__.name)


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


@singledispatch
def get_comment(entity: Union[TableProtocol, Column]) -> str:
    """Get comment on entity"""


@get_comment.register
def get_table_comment(entity: TableProtocol) -> str:
    """Get comment on entity"""
    return entity.__table__.comment or ""


@get_comment.register
def get_columne_comment(entity: Column) -> str:
    """Get comment on entity"""
    return entity.comment or ""


@lru_cache()
def is_nullable(relationship: RelationshipProperty) -> bool:
    """Checks if a sqlalchemy orm relationship is nullable"""
    for local_col, remote_col in relationship.local_remote_pairs:
        if local_col.nullable or remote_col.nullable:
            return True
    return False
