# pylint: disable=invalid-name
from __future__ import annotations

import secrets
import string
import typing
from functools import lru_cache
from flupy import flu

from cachetools import cached
from nebulo.config import Config
from nebulo.gql.alias import CompositeType, ConnectionType, ScalarType, TableType
from nebulo.gql.parse_info import ASTNode
from nebulo.gql.relay.cursor import to_cursor_sql
from nebulo.gql.relay.node_interface import NodeID, to_global_id_sql
from nebulo.sql.inspect import (
    get_columns,
    get_primary_key_columns,
    get_relationships,
    get_table_name,
)
from nebulo.sql.table_base import TableProtocol
from sqlalchemy import Column
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql.compiler import StrSQLCompiler
from sqlalchemy.dialects.postgresql import JSONB


from sqlalchemy import (
    text,
    column,
    select,
    literal_column,
    func,
    literal,
    and_,
    asc,
    desc,
    tuple_,
    table,
)
from sqlalchemy import create_engine
from sqlalchemy.sql.selectable import Alias
from sqlalchemy.sql.elements import Label


def sql_builder(tree: ASTNode, parent_name: typing.Optional[str] = None) -> Alias:
    return_type = tree.return_type

    # SQL Function handler
    if hasattr(return_type, "sql_function"):
        return return_type.sql_function.to_executable(tree.args)

    if isinstance(return_type, TableType):
        return row_block(field=tree, parent_name=parent_name)

    if isinstance(return_type, ConnectionType):
        return connection_block(field=tree, parent_name=parent_name)

    raise Exception("sql builder could not match return type")


def sanitize(text: str) -> str:
    escape_key = secure_random_string()
    return f"${escape_key}${text}${escape_key}$"


@lru_cache()
def field_name_to_column(sqla_model: TableProtocol, gql_field_name: str) -> Column:
    for column in get_columns(sqla_model):
        if Config.column_name_mapper(column) == gql_field_name:
            return column
    raise KeyError(f"No column corresponding to field {gql_field_name}")


@lru_cache()
def field_name_to_relationship(
    sqla_model: TableProtocol, gql_field_name: str
) -> RelationshipProperty:
    for relationship in get_relationships(sqla_model):
        if Config.relationship_name_mapper(relationship) == gql_field_name:
            return relationship
    raise Exception(f"No relationship corresponding to field {gql_field_name}")


def to_join_clause(field: ASTNode, parent_block_name: str) -> typing.List[str]:
    parent_field = field.parent
    assert parent_field is not None
    relation_from_parent = field_name_to_relationship(
        parent_field.return_type.sqla_model, field.name
    )
    local_table_name = get_table_name(field.return_type.sqla_model)

    join_clause = []
    for parent_col, local_col in relation_from_parent.local_remote_pairs:
        parent_col_name = parent_col.name
        local_col_name = local_col.name
        join_clause.append(
            text(
                f"{parent_block_name}.{parent_col_name} = {local_table_name}.{local_col_name}"
            )
        )
    return join_clause


def to_pkey_clause(field: ASTNode, pkey_eq: typing.List[str]) -> typing.List[str]:
    local_table = field.return_type.sqla_model
    local_table_name = get_table_name(field.return_type.sqla_model)
    pkey_cols = get_primary_key_columns(local_table)

    res = []
    for col, val in zip(pkey_cols, pkey_eq):
        res.append(f"{local_table_name}.{col.name} = {sanitize(val)}")
    return res


def to_limit(field: ASTNode) -> int:
    args = field.args
    default = 10
    first = int(args.get("first", default))
    last = int(args.get("last", default))
    limit = min(first, last, default)
    return limit


def to_conditions_clause(field: ASTNode) -> typing.List[str]:
    return_sqla_model = field.return_type.sqla_model
    local_table_name = get_table_name(return_sqla_model)
    args = field.args

    conditions = args.get("condition")

    if conditions is None:
        return [True]

    res = []
    for field_name, val in conditions.items():
        column_name = field_name_to_column(return_sqla_model, field_name).name
        res.append(text(f"{local_table_name}.{column_name} = {sanitize(val)}"))
    return res


def build_relationship(field: ASTNode, block_name: str) -> Label:
    return sql_builder(field, block_name).as_scalar().label(field.alias)


def sql_finalize(return_name: str, expr: str) -> str:
    final = select(
        [func.jsonb_build_object(literal(return_name), expr.c.ret_json).label("json")]
    ).select_from(expr)
    return final


def row_block(field: ASTNode, parent_name: typing.Optional[str] = None) -> str:
    return_type = field.return_type
    sqla_model = return_type.sqla_model
    core_model = sqla_model.__table__

    block_name = secure_random_string()
    if parent_name is None:
        # If there is no parent, nodeId is mandatory
        pkey_cols = get_primary_key_columns(sqla_model)
        _, pkey_eq = field.args["nodeId"]
        pkey_clause = [col == col_val for col, col_val in zip(pkey_cols, pkey_eq)]
        join_clause = [True]
    else:
        # If there is a parent no arguments are accepted
        join_clause = to_join_clause(field, parent_name)
        pkey_clause = [True]

    core_model_ref = (
        select(core_model.c).where(and_(*pkey_clause, *join_clause))
    ).alias(block_name)

    select_clause = []
    for subfield in field.fields:

        if subfield.return_type == NodeID:
            elem = select([text(str(to_global_id_sql(sqla_model)))]).label(
                subfield.alias
            )
            select_clause.append(elem)
        elif isinstance(subfield.return_type, (ScalarType, CompositeType)):
            col_name = field_name_to_column(sqla_model, subfield.name).name
            elem = core_model_ref.c[col_name].label(subfield.alias)
            select_clause.append(elem)
        else:
            elem = build_relationship(subfield, block_name)
            select_clause.append(elem)

    block = (
        select(
            [
                func.jsonb_build_object(
                    *flu(select_clause)
                    .map(lambda x: (literal(x.key), x))
                    .flatten()
                    .collect()
                ).label("ret_json")
            ]
        ).select_from(core_model_ref)
    ).alias()

    return block


def check_has_total(field: ASTNode) -> bool:
    "Check if 'totalCount' is requested in the query result set"
    return any(x.name in "totalCount" for x in field.fields)


def get_edge_node_fields(field):
    """Returns connection.edge.node fields"""
    for cfield in field.fields:
        if cfield.name == "edges":
            for edge_field in cfield.fields:
                if edge_field.name == "node":
                    return edge_field.fields
    return []


def build_scalar(field: ASTNode, sqla_model: TableProtocol) -> Label:
    return_type = field.return_type

    if return_type == NodeID:
        return select([text(str(to_global_id_sql(sqla_model)))]).label(field.alias)

    col = field_name_to_column(sqla_model, field.name)
    return sqla_model.__table__.c[col.name].label(field.alias)


def connection_block(field: ASTNode, parent_name: typing.Optional[str]) -> Alias:
    return_type = field.return_type
    sqla_model = return_type.sqla_model

    block_name = secure_random_string()
    if parent_name is None:
        join_conditions = [True]
    else:
        join_conditions = to_join_clause(field, parent_name)

    filter_conditions = to_conditions_clause(field)
    limit = to_limit(field)
    has_total = check_has_total(field)

    is_page_after = "after" in field.args
    is_page_before = "before" in field.args

    cursor = to_cursor_sql(sqla_model)

    totalCount_alias = field.get_subfield_alias(["totalCount"])

    edges_alias = field.get_subfield_alias(["edges"])
    node_alias = field.get_subfield_alias(["edges", "node"])
    cursor_alias = field.get_subfield_alias(["edges", "cursor"])

    pageInfo_alias = field.get_subfield_alias(["pageInfo"])
    hasNextPage_alias = field.get_subfield_alias(["pageInfo", "hasNextPage"])
    hasPreviousPage_alias = field.get_subfield_alias(["pageInfo", "hasPreviousPage"])
    startCursor_alias = field.get_subfield_alias(["pageInfo", "startCursor"])
    endCursor_alias = field.get_subfield_alias(["pageInfo", "endCursor"])

    # Apply Filters
    core_model = sqla_model.__table__
    core_model_ref = (
        select(core_model.c)
        .select_from(core_model)
        .where(
            and_(
                # Join clause
                *join_conditions,
                # Conditions
                *filter_conditions,
            )
        )
    ).alias(block_name)

    new_edge_node_selects = []
    new_relation_selects = []

    for subfield in get_edge_node_fields(field):
        # Does anything other than NodeID go here?
        if subfield.return_type == NodeID:
            return select([text(str(to_global_id_sql(sqla_model)))]).label(
                subfield.alias
            )
        elif isinstance(subfield.return_type, (ScalarType, CompositeType)):
            col_name = field_name_to_column(sqla_model, subfield.name).name
            elem = core_model_ref.c[col_name].label(subfield.alias)
            new_edge_node_selects.append(elem)
        else:
            elem = build_relationship(subfield, block_name)
            new_relation_selects.append(elem)

    # Setup Pagination
    args = field.args
    after_cursor = args.get("after", None)
    before_cursor = args.get("before", None)
    first = args.get("first", None)
    last = args.get("last", None)

    if after_cursor or before_cursor:
        local_table_name = get_table_name(field.return_type.sqla_model)
        cursor_table_name, cursor_values = before_cursor or after_cursor

        if after_cursor is not None and before_cursor is not None:
            raise ValueError('only one of "before" and "after" may be provided')

        if first is not None and last is not None:
            raise ValueError('only one of "first" and "last" may be provided')

        if after_cursor is not None and last is not None:
            raise ValueError('"after" is not compatible with "last". Use "first"')

        if before_cursor is not None and first is not None:
            raise ValueError('"before" is not compatible with "first". Use "last"')

        if after_cursor is None and before_cursor is None:
            return True

        if cursor_table_name != local_table_name:
            raise ValueError("Invalid cursor for entity type")

        pkey_cols = get_primary_key_columns(sqla_model)

        pagination_clause = (
            tuple_(*[core_model_ref.c[col.name] for col in pkey_cols])
            .op(">" if after_cursor is not None else "<")
            .tuple_(cursor_values)
        )
    else:
        pagination_clause = True

    order_clause = [
        asc(core_model_ref.c[col.name]) for col in get_primary_key_columns(sqla_model)
    ]
    reverse_order_clause = [
        desc(core_model_ref.c[col.name]) for col in get_primary_key_columns(sqla_model)
    ]

    total_block = (
        select([func.count(1).label("total_count")])
        .select_from(core_model_ref.alias())
        .where(has_total)
    ).alias(block_name + "_total")

    # Select the right stuff
    p1_block = (
        select(
            [
                *new_edge_node_selects,
                *new_relation_selects,
                # For internal Use
                # select([text(str(to_global_id_sql(sqla_model)))]).label("_nodeId"),
                select([1]).label("_nodeId"),
                # For internal Use
                func.row_number().over().label("_row_num"),
            ]
        )
        .select_from(core_model_ref)
        .where(pagination_clause)
        .order_by(
            *(reverse_order_clause if is_page_before else order_clause), *order_clause
        )
        .limit(limit + 1)
    ).alias(block_name + "_p1")

    # Drop maybe extra row

    p2_block = (select(p1_block.c).select_from(p1_block).limit(limit)).alias(
        block_name + "_p2"
    )

    ordering = (
        desc(literal_column("_row_num"))
        if is_page_before
        else asc(literal_column("_row_num"))
    )

    p3_block = (select(p2_block.c).select_from(p2_block).order_by(ordering)).alias(
        block_name + "_p3"
    )

    final = (
        select(
            [
                func.jsonb_build_object(
                    literal(totalCount_alias),
                    func.min(total_block.c.total_count) if has_total else None,
                    literal(pageInfo_alias),
                    func.jsonb_build_object(
                        # literal(hasNextPage_alias), text(f"(select count(*) from {block_name}) < ")(select has_next from has_next_page),
                        # literal(hasPreviousPage_alias), {'true' if is_page_after else 'false'},
                        literal(startCursor_alias),
                        func.array_agg(p3_block.c._nodeId)[1],
                        literal(endCursor_alias),
                        func.array_agg(p3_block.c._nodeId)[
                            func.array_upper(func.array_agg(p3_block.c._nodeId), 1)
                        ],
                    ),
                    literal(edges_alias),
                    func.coalesce(
                        func.jsonb_agg(
                            func.jsonb_build_object(
                                literal(cursor_alias),
                                p3_block.c._nodeId,
                                literal(node_alias),
                                func.cast(
                                    func.row_to_json(literal_column(p3_block.name)), JSONB()
                                ),
                            )
                        ),
                        func.cast(literal('[]'), JSONB())
                    )
                ).label("ret_json")
            ]
        )
        .select_from(p3_block)
        .select_from(total_block if has_total else select([1]).alias())
    ).alias()

    return final


def secure_random_string(length: int = 8) -> str:
    letters = string.ascii_lowercase
    return "".join([secrets.choice(letters) for _ in range(length)])
