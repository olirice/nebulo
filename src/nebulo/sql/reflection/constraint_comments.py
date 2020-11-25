from __future__ import annotations

from functools import lru_cache
from typing import Dict, Optional

from nebulo.sql.inspect import get_table_name
from sqlalchemy import text as sql_text
from sqlalchemy.engine import Engine
from sqlalchemy.sql.schema import Constraint

__all__ = ["populate_constraint_comment"]


SchemaName = str
TableName = str
ConstraintName = str
Comment = str

CommentMap = Dict[SchemaName, Dict[TableName, Dict[ConstraintName, Comment]]]


def populate_constraint_comment(engine: Engine, constraint: Constraint) -> None:
    """Adds SQL comments on a constraint to the SQLAlchemy constraint's
    Constraint.info['comment'] dictionary
    """

    schema: Optional[str] = constraint.table.schema
    table_name: str = get_table_name(constraint.table)
    constraint_name: Optional[str] = constraint.name

    if schema is None or constraint_name is None:
        return

    comment_map: CommentMap = reflect_all_constraint_comments(engine=engine, schema=schema)
    comment: Optional[str] = comment_map.get(schema, {}).get(table_name, {}).get(constraint_name)

    # constraint.info is "Optional[Mapping[str, Any]]"
    if not hasattr(constraint, "info"):
        constraint.info = {"comment": comment}
    else:
        constraint.info["comment"] = comment  # type: ignore

    return


@lru_cache()
def reflect_all_constraint_comments(engine, schema: str) -> CommentMap:
    """Collect a mapping of constraint comments"""

    sql = sql_text(
        """
    select
            c.relnamespace::regnamespace::text schemaname,
            c.relname tablename,
            t.conname constraintname,
            d.description comment_body
    from pg_class c
            join pg_constraint t
                    on c.oid = t.conrelid
            join pg_description d
                    on t.oid = d.objoid
                    and t.tableoid = d.classoid
    where
            c.relnamespace::regnamespace::text = :schema
    """
    )

    results = engine.execute(sql, schema=schema).fetchall()

    comment_map: CommentMap = {}

    for schema_name, table_name, constraint_name, comment in results:
        comment_map[schema_name] = comment_map.get(schema_name, {})
        comment_map[schema_name][table_name] = comment_map[schema_name].get(table_name, {})
        comment_map[schema_name][table_name][constraint_name] = comment

    return comment_map
