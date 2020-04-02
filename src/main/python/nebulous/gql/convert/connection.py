from __future__ import annotations

import typing
from functools import lru_cache

from sqlalchemy import func, literal, select

from ..alias import (
    Argument,
    EnumType,
    EnumValue,
    Field,
    InputField,
    InputObjectType,
    Int,
    List,
    NonNull,
    ObjectType,
)
from ..casing import snake_to_camel
from ..default_resolver import default_resolver
from .cursor import Cursor
from .page_info import PageInfo
from .total_count import TotalCount

if typing.TYPE_CHECKING:
    pass

__all__ = ["connection_factory"]


@lru_cache()
def connection_factory(sqla_model):
    name = f"{snake_to_camel(sqla_model.__table__.name)}Connection"

    from .table import table_factory
    from .edge import edge_factory

    table = table_factory(sqla_model)
    edge = edge_factory(sqla_model)

    def build_attrs():
        return {
            "nodes": Field(NonNull(List(table)), resolver=default_resolver),
            "edges": Field(NonNull(List(NonNull(edge))), resolver=default_resolver),
            "pageInfo": Field(NonNull(PageInfo), resolver=default_resolver),
            "totalCount": Field(NonNull(TotalCount), resolver=default_resolver),
        }

    return_type = ObjectType(name=name, fields=build_attrs, description="")
    return_type.sqla_model = sqla_model
    return return_type


def connection_args_factory(sqla_model):
    from .condition import condition_factory
    from .ordering import ordering_factory

    condition = condition_factory(sqla_model)
    ordering = ordering_factory(sqla_model)

    return {
        "first": Argument(Int, default_value=10, description="", out_name=None),
        # "last": Argument(Int),
        # "before": Argument(Cursor),
        "after": Argument(Cursor),
        "condition": Argument(condition),
        "orderBy": Argument(List(ordering)),
    }


def resolve_connection(tree, parent_query) -> typing.Tuple["SelectClause", "ConditionPartials"]:
    """Resolves a single record from a table"""
    from .sql_resolver import resolve_one
    from .cursor import resolve_cursor

    condition_partials = []

    fields = tree["fields"]

    # Apply Argument Filters
    query = select([parent_query])

    args = tree["args"]

    order_by = args.get("orderBy")
    if order_by is not None:
        order_clause = [direction(getattr(query.c, col_name)) for col_name, direction in order_by]
        query = query.order_by(*order_clause)

    # Allowed Args [first, last, ordering?, etc]
    first = args.get("first")
    if first is not None:
        query = query.limit(first)

    query = query.alias()

    # Always return the table name in each row
    builder = []

    for tree_field in fields:
        field_name = tree_field["name"]
        field_alias = tree_field["alias"]

        if field_name == "nodes":
            result_wrapper = lambda *x: func.json_agg(func.json_build_object(*x))
            builder.extend(
                [
                    literal(field_alias),
                    resolve_one(tree_field, query, result_wrapper=result_wrapper),
                ]
            )

        elif field_name == "edges":

            edge_builder = []
            edge_fields = tree_field["fields"]

            for edge_field in edge_fields:
                if edge_field["name"] == "node":
                    edge_field_alias = edge_field["alias"]
                    edge_builder.extend(
                        [
                            literal(edge_field_alias),  # nodes
                            # node query
                            resolve_one(edge_field, query, result_wrapper=func.json_build_object),
                        ]
                    )
                if edge_field["name"] == "cursor":
                    edge_field_alias = edge_field["alias"]
                    edge_builder.extend(
                        [
                            literal(edge_field_alias),
                            resolve_cursor(
                                query,
                                ordering=order_by or [],
                                sqla_model=tree["return_type"].sqla_model,
                            ),
                        ]
                    )

            builder.extend(
                [literal(field_alias), func.array_agg(func.json_build_object(*edge_builder))]
            )

        elif field_name == "pageInfo":
            print("Delegating for page info")

        else:
            raise NotImplementedError(f"Unreachable. No field {field_name} on connection")

    return func.json_build_object(*builder), condition_partials
