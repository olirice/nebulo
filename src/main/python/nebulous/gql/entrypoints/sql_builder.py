import random
import string
import typing

from nebulous.gql.convert.cursor import to_cursor_sql
from nebulous.gql.convert.node_interface import to_global_id_sql

from ..alias import ConnectionType, ScalarType, TableType
from ..convert.node_interface import NodeID


def to_join_clause(field, parent_block_name: str) -> typing.List[str]:  #
    parent_field = field.parent
    relation_from_parent = getattr(parent_field.return_type.sqla_model, field.name).property
    local_table_name = field.return_type.sqla_model.table_name

    join_clause = []
    for parent_col, local_col in relation_from_parent.local_remote_pairs:
        parent_col_name = parent_col.name
        local_col_name = local_col.name
        join_clause.append(
            f"{parent_block_name}.{parent_col_name} = {local_table_name}.{local_col_name}"
        )
    return join_clause


def to_pkey_clause(field, pkey_eq) -> typing.List[str]:
    local_table = field.return_type.sqla_model
    local_table_name = field.return_type.sqla_model.table_name
    pkey_cols = list(local_table.primary_key.columns)

    if not hasattr(pkey_eq, "__iter__"):
        pkey_eq = [pkey_eq]

    res = []
    for col, val in zip(pkey_cols, pkey_eq):
        res.append(f"{local_table_name}.{col.name} = {val}")

    return res


def to_after_clause(field) -> typing.List[str]:
    local_table = field.return_type.sqla_model
    local_table_name = field.return_type.sqla_model.table_name

    pkey_cols = list(local_table.primary_key.columns)

    args = field.args
    cursor = args.get("after", None)
    if cursor is None:
        return "true"
    cursor_table, cursor_values = cursor
    # if not hasattr(cursorpkey_eq, "__iter__"):
    #    pkey_eq = [pkey_eq]

    if cursor_table != local_table_name:
        raise ValueError("Invalid after cursor")

    left = "(" + ", ".join([x.name for x in pkey_cols]) + ")"
    right = "(" + ", ".join(cursor_values) + ")"

    return left + " > " + right


def to_limit_clause(field) -> int:
    args = field.args
    limit = args.get("first", 10)
    return limit


def to_conditions_clause(field) -> typing.List[str]:
    local_table_name = field.return_type.sqla_model.table_name
    args = field.args

    conditions = args.get("condition")

    if conditions is None:
        return ["true"]

    res = []
    for col_name, val in conditions.items():
        res.append(f"{local_table_name}.{col_name} = {val}")
    return res


def build_scalar(field, sqla_model) -> typing.Tuple[str, str]:
    return_type = field.return_type
    if return_type == NodeID:
        return (field.name, to_global_id_sql(sqla_model))
    return (field.name, getattr(sqla_model, field.name).name)


def build_relationship(field, block_name):
    return (field.name, sql_builder(field, block_name))


def sql_builder(tree, parent_name=None):
    return_type = tree.return_type
    sqla_model = return_type.sqla_model

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

    block_name = random_string()
    table_name = sqla_model.table_name
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
    return ", ".join([x.name for x in sqla_model.primary_key.columns])


def connection_block(field, parent_name):
    return_type = field.return_type
    sqla_model = return_type.sqla_model

    block_name = random_string()
    table_name = sqla_model.table_name
    if parent_name is None:
        join_conditions = ["true"]
    else:
        join_conditions = to_join_clause(field, parent_name)

    filter_conditions = to_conditions_clause(field)
    limit = to_limit_clause(field)
    after = to_after_clause(field)
    order = to_order_clause(field)
    cursor = to_cursor_sql(sqla_model)

    nodes_selects = []
    edge_node_selects = []
    for cfield in field.fields:
        if cfield.name in "nodes":
            subfields = cfield.fields
        elif cfield.name == "edges":
            subfields = [x for x in cfield.fields if x.name == "node"][0].fields
        elif cfield.name == "pageInfo":
            # pageInfo is always retrieved from the database
            continue

        for subfield in subfields:
            if isinstance(subfield.return_type, ScalarType):
                elem = build_scalar(subfield, sqla_model)
            else:
                elem = build_relationship(subfield, block_name)
            if cfield.name == "nodes":
                nodes_selects.append(elem)
            elif cfield.name == "edges":
                edge_node_selects.append(elem)

    # check if cursor is required

    block = f"""
(
    with {block_name}_p1 as (
        select *
        from {table_name}
        where 
            ({"and".join(join_conditions) or 'true'})
            and ({"and".join(filter_conditions) or 'true'})
            and ({after or 'true'})
        order by
            {order}
        limit
            {min(limit, 10) + 1}
    ),
    {block_name} as (
        select row_number() over () as row_num, *
        from {block_name}_p1
        limit {min(limit, 10)}
    ),
    has_next_page as (
        select (select count(*) from {block_name}) > (select count(*) from {block_name}) as has_next
    )

    select
        jsonb_build_object(
            'pageInfo', json_build_object(
                'hasNextPage', (select has_next from has_next_page),
                'hasPreviousPage', {'true' if after else 'false'},
                'startCursor', (select {cursor} from {block_name} order by row_num asc limit 1),
                'endCursor', (select {cursor} from {block_name} order by row_num desc limit 1)
            ),
            'nodes', json_agg(
                jsonb_build_object(
                    {", ".join([f"'{name}', {expr}" for name, expr in nodes_selects])}
                )
            ),
            'edges', json_agg(
                jsonb_build_object(
                    'cursor', {cursor}, 
                    'node', json_build_object(
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


def random_string(length=8):
    letters = string.ascii_lowercase
    return "".join(random.choices(letters, k=length))
