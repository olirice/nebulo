# pylint: disable=invalid-name
from __future__ import annotations

import secrets
import string
import typing

from nebulo.gql.alias import ConnectionType, ScalarType, TableType
from nebulo.gql.convert.cursor import to_cursor_sql
from nebulo.gql.convert.node_interface import NodeID, to_global_id_sql
from nebulo.sql.inspect import get_primary_key_columns, get_table_name

if typing.TYPE_CHECKING:
    from sqlalchemy.sql.compiler import StrSQLCompiler


def sanitize(text: str) -> str:
    escape_key = secure_random_string()
    return f"${escape_key}${text}${escape_key}$"


def to_join_clause(field, parent_block_name: str) -> typing.List[str]:  #
    parent_field = field.parent
    relation_from_parent = getattr(parent_field.return_type.sqla_model, field.name).property
    local_table_name = get_table_name(field.return_type.sqla_model)

    join_clause = []
    for parent_col, local_col in relation_from_parent.local_remote_pairs:
        parent_col_name = parent_col.name
        local_col_name = local_col.name
        join_clause.append(f"{parent_block_name}.{parent_col_name} = {local_table_name}.{local_col_name}")
    return join_clause


def to_pkey_clause(field, pkey_eq) -> typing.List[str]:
    local_table = field.return_type.sqla_model
    local_table_name = get_table_name(field.return_type.sqla_model)
    pkey_cols = get_primary_key_columns(local_table)

    if not hasattr(pkey_eq, "__iter__"):
        pkey_eq = [pkey_eq]

    res = []
    for col, val in zip(pkey_cols, pkey_eq):
        res.append(f"{local_table_name}.{col.name} = {sanitize(val)}")
    return res


def to_after_clause(field) -> str:
    local_table = field.return_type.sqla_model
    local_table_name = get_table_name(field.return_type.sqla_model)

    pkey_cols = get_primary_key_columns(local_table)

    args = field.args
    cursor = args.get("after", None)
    if cursor is None:
        return "true"
    cursor_table, cursor_values = cursor
    sanitized_cursor_values = [sanitize(x) for x in cursor_values]

    if cursor_table != local_table_name:
        raise ValueError("Invalid after cursor")

    # No user input
    left = "(" + ", ".join([x.name for x in pkey_cols]) + ")"

    # Contains user input
    right = "(" + ", ".join(sanitized_cursor_values) + ")"

    return left + " > " + right


def to_limit_clause(field) -> int:
    args = field.args
    limit = int(args.get("first", 10))
    return limit


def to_conditions_clause(field) -> typing.List[str]:
    return_sqla_model = field.return_type.sqla_model
    local_table_name = get_table_name(return_sqla_model)
    args = field.args

    conditions = args.get("condition")

    if conditions is None:
        return ["true"]

    res = []
    for col_key, val in conditions.items():
        col_name = getattr(return_sqla_model, col_key).name
        res.append(f"{local_table_name}.{col_name} = {sanitize(val)}")
    return res


def build_scalar(field, sqla_model) -> typing.Tuple[str, typing.Union[str, StrSQLCompiler]]:
    return_type = field.return_type
    if return_type == NodeID:
        return (field.alias, to_global_id_sql(sqla_model))
    return (field.alias, getattr(sqla_model, field.name).name)


def build_relationship(field, block_name):
    return (field.name, sql_builder(field, block_name))


def sql_builder(tree, parent_name=None):
    return_type = tree.return_type

    if isinstance(return_type, TableType):
        return row_block(field=tree, parent_name=parent_name)

    if isinstance(return_type, ConnectionType):
        return connection_block(field=tree, parent_name=parent_name)


def sql_finalize(return_name, expr):
    return f"""select
    jsonb_build_object('{return_name}', ({expr}))
    """


def row_block(field, parent_name=None):
    return_type = field.return_type
    sqla_model = return_type.sqla_model

    block_name = secure_random_string()
    table_name = get_table_name(sqla_model)
    if parent_name is None:
        # If there is no parent, nodeId is mandatory
        _, pkey_eq = field.args["nodeId"]
        pkey_clause = to_pkey_clause(field, pkey_eq)
        join_clause = ["true"]
    else:
        # If there is a parent no arguments are accepted
        join_clause = to_join_clause(field, parent_name)
        pkey_clause = ["true"]

    select_clause = []
    for field in field.fields:
        if isinstance(field.return_type, ScalarType):
            select_clause.append(build_scalar(field, sqla_model))
        else:
            select_clause.append(build_relationship(field, block_name))

    block = f"""
(
    with {block_name} as (
        select
            *
        from
            {table_name}
        where
            ({" and ".join(pkey_clause)})
            and ({" and ".join(join_clause)})
    )
    select
        jsonb_build_object({", ".join([f"'{name}', {expr}" for name, expr in select_clause])})
    from
        {block_name}
)
    """
    return block


def to_order_clause(field):
    sqla_model = field.return_type.sqla_model
    return ", ".join([x.name for x in get_primary_key_columns(sqla_model)])


def check_has_total(field) -> bool:
    "Check if 'totalCount' is requested in the query result set"
    return any(x.name in "totalCount" for x in field.fields)


def get_selection_alias(field, key: str) -> str:
    """ Looks up the alias of a selected subfield, or returns subfield.name
    if no alias is provided """
    for subfield in field.fields:
        if subfield.name == key:
            return subfield.alias or key
    return key


def connection_block(field, parent_name):
    return_type = field.return_type
    sqla_model = return_type.sqla_model

    block_name = secure_random_string()
    table_name = get_table_name(sqla_model)
    if parent_name is None:
        join_conditions = ["true"]
    else:
        join_conditions = to_join_clause(field, parent_name)

    filter_conditions = to_conditions_clause(field)
    limit = to_limit_clause(field)
    after = to_after_clause(field)
    order = to_order_clause(field)
    has_total = check_has_total(field)

    cursor = to_cursor_sql(sqla_model)

    totalCount_alias = field.get_subfield_alias(["totalCount"])

    edges_alias = field.get_subfield_alias(["edges"])
    node_alias = field.get_subfield_alias(["edges", "node"])
    cursor_alias = field.get_subfield_alias(["edges", "cursor"])

    pageInfo_alias = sanitize(field.get_subfield_alias(["pageInfo"]))
    hasNextPage_alias = sanitize(field.get_subfield_alias(["pageInfo", "hasNextPage"]))
    hasPreviousPage_alias = sanitize(field.get_subfield_alias(["pageInfo", "hasPreviousPage"]))
    startCursor_alias = sanitize(field.get_subfield_alias(["pageInfo", "startCursor"]))
    endCursor_alias = sanitize(field.get_subfield_alias(["pageInfo", "endCursor"]))

    edge_node_selects = []
    for cfield in field.fields:
        if cfield.name == "edges":
            for edge_field in cfield.fields:
                if edge_field.name == "node":
                    for subfield in edge_field.fields:
                        # Does anything other than NodeID go here?
                        if isinstance(subfield.return_type, ScalarType):
                            elem = build_scalar(subfield, sqla_model)
                        else:
                            elem = build_relationship(subfield, block_name)
                        if cfield.name == "edges":
                            edge_node_selects.append(elem)
                        # Other than edges, pageInfo, and cursor stuff is
                        # all handled by default

    block = f"""
(
    with total as (
        select
            count(*) total_count
        from
            {table_name}
        where
            -- Join Clause
            ({"and".join(join_conditions) or 'true'})
            -- Conditions
            and ({"and".join(filter_conditions) or 'true'})
            -- Skip if not requested
            and {'true' if has_total else 'false'}
    ),

    {block_name}_p1 as (
        select *
        from {table_name}
        where
            ({"and".join(join_conditions) or 'true'})
            and ({"and".join(filter_conditions) or 'true'})
            and ({after or 'true'})
        order by
            {order}
        limit
            {limit + 1}
    ),

    {block_name} as (
        select row_number() over () as row_num, *
        from {block_name}_p1
        limit {limit}
    ),

    has_next_page as (
        select (select count(*) from {block_name}) > (select count(*) from {block_name}) as has_next
    )
/*
    has_previous_page as (
        select
            case
                -- If a cursor is provided, that row appears on the previous page
                when coalesce(before_cursor, after_cursor) is not null then true
                -- If no cursor is provided, no previous page
                else false
            end has_previous
    ),
*/
    select
        jsonb_build_object(
            '{totalCount_alias}', (select total_count from total),

            '{pageInfo_alias}', json_build_object(
                '{hasNextPage_alias}', (select has_next from has_next_page),
                '{hasPreviousPage_alias}', {'true' if after else 'false'},
                '{startCursor_alias}', (select {cursor} from {block_name} order by row_num asc limit 1),
                '{endCursor_alias}', (select {cursor} from {block_name} order by row_num desc limit 1)
            ),
            '{edges_alias}', json_agg(
                jsonb_build_object(
                    '{cursor_alias}', {cursor},
                    '{node_alias}', json_build_object(
                        {", ".join([f"'{name}', {expr}" for name, expr in edge_node_selects])}
                    )
                )
            )
        )
    from
        {block_name}
)
    """
    return block


def secure_random_string(length=8):
    letters = string.ascii_lowercase
    return "".join([secrets.choice(letters) for _ in range(length)])
