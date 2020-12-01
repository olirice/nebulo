# pylint: disable=unsubscriptable-object, invalid-name
from __future__ import annotations

from functools import lru_cache
from typing import Callable, List, Optional, Union

from nebulo.sql.table_base import TableProtocol
from sqlalchemy import Column, ForeignKeyConstraint, Table
from sqlalchemy import inspect as sql_inspect
from sqlalchemy.orm import Mapper, RelationshipProperty
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


@lru_cache()
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


@lru_cache()
def get_foreign_key_constraints(entity: Union[TableProtocol, Table]) -> List[ForeignKeyConstraint]:
    """Retrieve all foreign keys associated with the table"""
    constraints = get_constraints(entity)
    fkeys = [x for x in constraints if isinstance(x, ForeignKeyConstraint)]
    return fkeys


@lru_cache()
def get_foreign_key_constraint_from_relationship(relationship: RelationshipProperty) -> Optional[ForeignKeyConstraint]:
    """Get the ForeignKeyConstraint that backs the input RelationshipProperty

    Note: the resolution method checks that the columns associated with the relationship
        match the columns associated with the foreign key constraint. If two identical
        foreign keys exist (they never should), the behavior is undefined
    """
    local_cols = list(relationship.local_columns)
    remote_cols = list(relationship.remote_side)

    # All columns associated with the relationship
    relationship_cols = set([*local_cols, *remote_cols])

    local_table: Table = local_cols[0].table
    remote_table: Table = remote_cols[0].table

    possible_fkeys = [
        *get_foreign_key_constraints(local_table),
        *get_foreign_key_constraints(remote_table),
    ]

    for fkey in possible_fkeys:

        # All local and remote columns associated with the primary key
        fkey_involved_cols = set([*list(fkey.columns), *[x.column for x in fkey.elements]])

        if relationship_cols == fkey_involved_cols:
            return fkey
    return None


@lru_cache()
def to_table(entity: Union[Table, TableProtocol, Mapper, Callable[[], Union[TableProtocol, Table]]]) -> Table:
    """Coerces Table and ORM Table to Table"""
    if isinstance(entity, Table):
        return entity
    elif isinstance(entity, Mapper):
        return to_table(entity.class_)
    elif isinstance(entity, TableProtocol):
        return entity.__table__
    elif callable(entity):
        return to_table(entity())
    raise NotImplementedError("invalid input type")
