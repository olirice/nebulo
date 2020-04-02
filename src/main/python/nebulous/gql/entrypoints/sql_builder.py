import random
import string
import typing

from ..alias import ConnectionType, ScalarType, TableType


def to_join_clause(field, parent_block_name: str) -> typing.List[str]:  #
    parent_field = field["parent"]
    relation_from_parent = getattr(parent_field["return_type"].sqla_model, field["name"]).property
    local_table_name = field["return_type"].sqla_model.table_name

    join_clause = []
    for parent_col, local_col in relation_from_parent.local_remote_pairs:
        parent_col_name = parent_col.name
        local_col_name = local_col.name
        join_clause.append(
            f"{parent_block_name}.{parent_col_name} = {local_table_name}.{local_col_name}"
        )
    return join_clause


def to_pkey_clause(field, pkey_eq) -> typing.List[str]:
    local_table = field["return_type"].sqla_model
    local_table_name = field["return_type"].sqla_model.table_name
    pkey_cols = list(local_table.primary_key.columns)

    if not hasattr(pkey_eq, "__iter__"):
        pkey_eq = [pkey_eq]

    res = []
    for col, val in zip(pkey_cols, pkey_eq):
        res.append(f"{local_table_name}.{col.name} = {val}")

    return res


def sql_builder(tree, parent_name=None):
    return_type = tree["return_type"]
    sqla_model = return_type.sqla_model

    # from ..convert.connection import ConnectionType

    if isinstance(return_type, TableType):
        block_name = random_string()
        table_name = sqla_model.table_name
        if parent_name is None:
            _, pkey_eq = tree["args"]["nodeId"]
            pkey_clause = to_pkey_clause(tree, pkey_eq)
            join_clause = ["true"]
        else:
            join_clause = to_join_clause(tree, parent_name)
            pkey_clause = ["true"]

        select_clause = []
        for field in tree["fields"]:
            if isinstance(field["return_type"], ScalarType):
                select_clause.append((field["name"], getattr(sqla_model, field["name"]).name))
            else:
                select_clause.append((field["name"], sql_builder(field, block_name)))

        return single_block(
            block_name=block_name,
            table_name=table_name,
            pkey_clause=pkey_clause,
            join_clause=join_clause,
            select_clause=select_clause,
        )

    if isinstance(return_type, ConnectionType):
        block_name = random_string()
        table_name = sqla_model.table_name
        if parent_name is None:
            join_conditions = ["true"]
        else:
            join_conditions = to_join_clause(tree, parent_name)

        filter_conditions = []

        nodes_selects = []
        edge_node_selects = []
        for field in tree["fields"]:
            if field["name"] == "nodes":
                subfields = field["fields"]
            elif field["name"] == "edges":
                subfields = [x for x in field["fields"] if x["name"] == "edges"][0]

            for subfield in subfields:
                if isinstance(subfield["return_type"], ScalarType):
                    elem = (subfield["name"], getattr(sqla_model, subfield["name"]).name)
                else:
                    elem = (subfield["name"], sql_builder(subfield, block_name))
                if field["name"] == "nodes":
                    nodes_selects.append(elem)
                elif field["name"] == "edges":
                    edge_node_selects.append(elem)

        return connection_block(
            block_name=block_name,
            table_name=table_name,
            join_conditions=join_conditions,
            filter_conditions=filter_conditions,
            nodes_selects=nodes_selects,
            edge_node_selects=edge_node_selects,
        )


def sql_finalize(return_name, expr):
    return f"""
select
    jsonb_build_object('{return_name}', ({expr}))
    """


def single_block(
    block_name: str, table_name, pkey_clause, join_clause, select_clause: typing.List[str]
):
    block = f"""
(
    with {block_name} as (
        select *
        from {table_name}
        where ({" and ".join(pkey_clause)}) and ({" and ".join(join_clause)})
    )
    select
        jsonb_build_object({", ".join([f"'{name}', {expr}" for name, expr in select_clause])})
    from
        {block_name}
) 
    """

    return block


def connection_block(
    block_name: str,
    table_name: str,
    join_conditions: typing.List[str],
    filter_conditions: typing.List[str],
    nodes_selects: typing.List[typing.Tuple[str, "expr"]],
    edge_node_selects: typing.List[typing.Tuple[str, "expr"]],
):
    block = f"""
(
    with {block_name} as (
        select *
        from {table_name}
        where {"and".join(join_conditions) or 'true'} and {"and".join(filter_conditions) or 'true'}
    )
    select
        jsonb_build_object(
            'pageInfo', json_build_object(
                'hasNextPage', null,
                'hasPreviousPage', null,
                'startCursor', null,
                'endCursor', null
            ),
            'nodes', json_agg(
                jsonb_build_object(
                    {", ".join([f"'{name}', {expr}" for name, expr in nodes_selects])}
                )
            ),
            'edges', json_agg(
                jsonb_build_object(
                    'cursor', null, 
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
