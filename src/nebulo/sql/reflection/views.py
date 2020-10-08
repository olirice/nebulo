# pylint: disable=unused-argument,invalid-name,line-too-long,unsubscriptable-object
from __future__ import annotations

from typing import List

from nebulo.sql.reflection.names import rename_table
from nebulo.sql.table_base import TableProtocol
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint, Table
from sqlalchemy import text as sql_text


class ViewMixin:
    """Mixin to differentiate views from tables"""

    is_view = True


def reflect_views(engine, schema, declarative_base) -> List[TableProtocol]:
    """Reflect SQLAlchemy ORM Tables from the database"""

    sql = sql_text(
        """
    select
	    relname view_name, description view_comment
    from
	    pg_views v
	    left join pg_description c
		    on true
	    left join pg_class on c.objoid = pg_class.oid
	    left join pg_namespace on pg_class.relnamespace = pg_namespace.oid
    where
	    v.viewname = relname
	    and nspname= :schema
    """
    )
    rows = engine.execute(sql, schema=schema).fetchall()

    views: List[TableProtocol] = []

    for view_name, view_comment in rows:
        primary_key_constraint = reflect_virtual_primary_key_constraint(view_comment)
        foreign_key_constraints = reflect_virtual_foreign_key_constraints(view_comment)

        # Reflect view as base table
        view_tab = Table(
            view_name,
            declarative_base.metadata,
            schema=schema,
            autoload=True,
            autoload_with=engine,
            *[primary_key_constraint],
            *foreign_key_constraints,
        )

        class_name = rename_table(declarative_base, view_name, view_tab)

        # ORM View Table
        view_orm = type(
            class_name,
            (
                declarative_base,
                ViewMixin,
            ),
            {"__table__": view_tab},
        )
        views.append(view_orm)  # type: ignore

    return views


def reflect_virtual_primary_key_constraint(comment: str) -> PrimaryKeyConstraint:
    """
    Reflects virtual primary key constraints from view comments

    Format:
        @primary_key (id, key2)'
    """
    for row in comment.split("\n"):
        if not row.startswith("@primary_key"):
            continue

        # Remove all spaces
        # Ex: @primary_key(id)
        row = row.replace(" ", "")

        # Ex: (variant_id)referencespublic.variant(id)
        col_names = row.split("(")[1].strip().strip(")").split(",")
        return PrimaryKeyConstraint(*col_names)

    raise Exception("Views must have a @primary_key comment")


def reflect_virtual_foreign_key_constraints(comment: str) -> List[ForeignKeyConstraint]:
    """
    Reflects virtual foreign key constraints from view comments

    Format:
        @foreign_key (variant_id, key2) references public.variant (id, key2)'

    """
    foreign_keys = []
    for row in comment.split("\n"):
        if not row.startswith("@foreign_key"):
            continue

        # Remove all spaces
        # Ex: @foreign_key(variant_id)referencespublic.variant(id)
        row = row.replace(" ", "")

        # Ex: (variant_id)referencespublic.variant(id)
        row = row.strip("@foreign_key")

        # Ex: ('(variant_id', 'public.variant(id)')
        local, remote = row.split(")references")

        # Ex: ['variant_id']
        local_col_names = local.lstrip("(").split(",")

        # Ex: ('public.variant', 'id)')
        remote_table, remote = remote.lstrip("references").split("(")
        remote_col_names = remote.strip().rstrip(")").split(",")

        remote_qualified_col_names = [f"{remote_table}.{remote_col_name}" for remote_col_name in remote_col_names]
        foreign_key = ForeignKeyConstraint(local_col_names, remote_qualified_col_names)
        foreign_keys.append(foreign_key)
    return foreign_keys
