from __future__ import annotations

import typing
from functools import lru_cache

from sqlalchemy import cast, func, literal, literal_column, select

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
        "first": Argument(Int, description="", out_name=None),
        "last": Argument(Int),
        "before": Argument(Cursor),
        "after": Argument(Cursor),
        "condition": Argument(condition),
        "orderBy": Argument(List(ordering)),
    }


def resolve_connection(tree, parent_query) -> typing.Tuple["SelectClause", "ConditionPartials"]:
    """Resolves a connection types

    Arguments:
        First, Last, OrderBy, Before, and After are applied to selectors
        but not to total count

    """
    from .sql_resolver import resolve_one
    from .cursor import resolve_cursor

    sqla_model = tree["return_type"].sqla_model

    # Apply Argument Filters
    base_query = select([parent_query])

    fields = tree["fields"]

    args = tree["args"]
    print(args)

    # Conditions are applied
    # To all fields, including totalCount, so they added
    # to the parent query

    # Conditions
    conditions = args.get("condition")
    if conditions is not None:
        print(conditions)
        for column_name, value in conditions.items():
            base_query = base_query.where(getattr(base_query.c, column_name) == value)

    base_query = base_query.cte()

    # Create a query branch for non-totalCount elements
    query = select([base_query])

    # Ordering subqueries
    # Allowed Args [first, last, ordering?, etc]
    # Validate Allowed Argument Combinations
    order_by = args.get("orderBy")

    first = args.get("first")
    last = args.get("last")
    before = args.get("before")
    after = args.get("after")

    if first is not None and last is not None:
        raise ValueError("Only one of first/last may be provided")
    if before is not None and after is not None:
        raise ValueError("Only one of before/after may be provided")
    if first is not None and before is not None:
        raise ValueError('First should only be used with "after" cursor')
    if last is not None and after is not None:
        raise ValueError('Last should only be used with "before" cursor')
    if last is not None and before is None:
        raise ValueError('A "before" cursor is required when "last" is provided')

    mode = "last" if last is not None or before is not None else "first"
    # Restrict page size and/or apply default
    first, last = min(first or 0, 20), min(last or 0, 20)

    from sqlalchemy import tuple_, asc, desc
    from sqlalchemy.sql.operators import gt, lt
    from sqlalchemy import asc, desc

    if mode == "first":
        if after is not None:
            # Ordering
            _, cursor_ordering, cursor_pkey = after
            for column in sqla_model.primary_key.columns:
                cursor_ordering.append((column.name, asc))
            cursor_order_clause = [
                direction(getattr(query.c, col_name)) for col_name, direction in cursor_ordering
            ]
            query = query.order_by(*cursor_order_clause)

            if cursor_ordering[0][1] == asc:
                comparator = gt
            else:
                comparator = lt

            # PKey location
            column_selector = []
            column_values = []
            for column, value in zip(sqla_model.primary_key.columns, cursor_pkey):
                column_selector.append(literal_column(column.name))
                column_values.append(cast(value, column.type))

            query = query.where(comparator(tuple_(*column_selector), tuple_(*column_values)))

        query = query.limit(first)

    else:
        # "last" mode
        _, cursor_ordering, cursor_pkey = before

        for column in sqla_model.primary_key.columns:
            cursor_ordering.append((column.name, desc))
        # Ordering
        cursor_order_clause = []
        for col_name, direction in cursor_ordering:
            inv_direction = desc if direction == asc else asc
            cursor_order_clause.append(inv_direction(getattr(query.c, col_name)))
        query = query.order_by(*cursor_order_clause)

        if cursor_ordering[0][1] == desc:
            comparator = gt
        else:
            comparator = lt

        # PKey location
        column_selector = []
        column_values = []
        for column, value in zip(sqla_model.primary_key.columns, cursor_pkey):
            column_selector.append(literal_column(column.name))
            column_values.append(cast(value, column.type))

        query = query.where(comparator(tuple_(*column_selector), tuple_(*column_values)))
        query = query.limit(last)

    query = query.cte()

    # Wrap it in another cte to preserve cursor ordering
    query = select([query])

    # Apply output ordering
    if order_by is not None:
        order_clause = [direction(getattr(query.c, col_name)) for col_name, direction in order_by]
        query = query.order_by(*order_clause)

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

        elif field_name == "totalCount":
            builder.extend(
                [
                    literal(field_alias),
                    select([func.count(literal(1))]).select_from(base_query).label("w"),
                ]
            )
        else:
            raise NotImplementedError(f"Unreachable. No field {field_name} on connection")

    return func.json_build_object(*builder)
