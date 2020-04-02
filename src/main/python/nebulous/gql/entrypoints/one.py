from sqlalchemy import func, select
from sqlalchemy.sql.expression import literal, literal_column

from ..alias import Argument, Field, ResolveInfo, ConnectionType
from ..convert.node_interface import NodeID
from ..convert.sql_resolver import resolve_one
from ..convert.table import table_factory
from ..parse_info import parse_resolve_info
from .utils import print_json, print_query
import typing


def one_node_factory(sqla_model) -> Field:
    node = table_factory(sqla_model)
    return Field(
        node, args={"nodeId": Argument(NodeID)}, resolver=cte_resolver, description=""
    )


def cte_resolver(_, info: ResolveInfo, **kwargs):
    context = info.context
    session = context["session"]

    tree = parse_resolve_info(info)
    # print(tree)

    # standard_query = build_standard_query(tree, None)
    # query = build_json_query(tree, standard_query)
    query = finalize(tree["name"], sql_builder(tree))
    print(query)
    result = session.execute(query).fetchone()[0]

    # print_query(query)

    # compiled_query = query.compile(compile_kwargs={"literal_binds": False})
    # bind_params = compiled_query.params
    # result = session.execute(query, bind_params).fetchone()[0]

    print_json(result)

    # Stash result on context so enable dumb resolvers to not fail
    context["result"] = result
    return result


def lpad_str(string, pad=0):
    lines = string.split("\n")
    return "\n".join([" " * pad + x for x in lines])


def sql_builder(tree, parent_name=None):
    fields = tree["fields"]
    return_type = tree["return_type"]
    sqla_model = return_type.sqla_model
    relation_keys = {rel.key for rel in sqla_model.relationships}

    from ..alias import EdgeType, ObjectType, ScalarType, TableType, ConnectionType
    from ..convert.cursor import Cursor
    from ..convert.node_interface import NodeID
    from ..convert.page_info import PageInfo

    # from ..convert.connection import ConnectionType

    if isinstance(return_type, TableType):
        block_name = random_string()
        table_name = sqla_model.table_name
        pkey_col_name = list(sqla_model.primary_key.columns)[0].name
        if parent_name is None:
            _, where_eq_pkey = tree["args"]["nodeId"]
        else:
            # _, where_eq_pkey = (relationship column from parent)
            raise NotImplementedError()

        select_clause = []
        for field in tree["fields"]:
            if isinstance(field["return_type"], ScalarType):
                select_clause.append(
                    (field["name"], getattr(sqla_model, field["name"]).name)
                )
            else:
                select_clause.append((field["name"], sql_builder(field, block_name)))

            # TODO(OR): Handle recursive single node
        return single_block(
            block_name=block_name,
            table_name=table_name,
            pkey_col_name=pkey_col_name,
            where_eq_pkey=where_eq_pkey,
            select_clause=select_clause,
        )

    if isinstance(return_type, ConnectionType):
        block_name = random_string()
        table_name = sqla_model.table_name
        pkey_col_name = list(sqla_model.primary_key.columns)[0].name
        if parent_name is None:
            join_conditions = ["true"]
        else:
            # TODO(OR): Generic
            join_conditions = [f"{parent_name}.id = {table_name}.account_id"]

        filter_conditions = []

        nodes_selects = []
        edge_node_selects = []
        for field in tree["fields"]:
            working = []
            if field["name"] == "nodes":
                subfields = field["fields"]
            elif field["name"] == "edges":
                subfields = [x for x in field["fields"] if x["name"] == "edges"][0]

            for subfield in subfields:
                if isinstance(subfield["return_type"], ScalarType):
                    elem = (
                        subfield["name"],
                        getattr(sqla_model, subfield["name"]).name,
                    )
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


def finalize(return_name, expr):
    return f"""
select
    jsonb_build_object('{return_name}', ({expr}))
    """


def single_block(
    block_name: str,
    table_name,
    pkey_col_name,
    where_eq_pkey,
    select_clause: typing.List[str],
    level=0,
):
    block = f"""
(
    with {block_name} as (
        select *
        from {table_name}
        where {pkey_col_name} = {where_eq_pkey} -- <NodeID> or <outer table ref clause>
    )
    select
        jsonb_build_object({", ".join([f"'{name}', {expr}" for name, expr in select_clause])})
    from
        {block_name}
) 
    """

    return lpad_str(block, level * 8)


def connection_block(
    block_name: str,
    table_name: str,
    join_conditions: typing.List[str],
    filter_conditions: typing.List[str],
    nodes_selects: typing.List[typing.Tuple[str, "expr"]],
    edge_node_selects: typing.List[typing.Tuple[str, "expr"]],
    level=0,
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

    return lpad_str(block, level * 8)


def unnest_maybe_nested_fields(tree):
    return_type = tree["return_type"]

    if not isinstance(return_type, ConnectionType):
        return tree["fields"]

    # Handle Connection Types
    return_fields = []
    con_fields = tree["fields"]
    for field in con_fields:
        field_name = field["name"]
        # Everything available on a connection is an object except totalCount
        if field_name == "totalCount":
            return_fields.append(field)
        else:
            return_fields.extend(field["fields"])
    return return_fields


def get_join_columns(tree, selectable):
    """Look ahead in the tree and return a list of columns that need to be in the
    current query so they are available for joining in lower queries"""

    fields = unnest_maybe_nested_fields(tree)
    return_type = tree["return_type"]
    sqla_model = return_type.sqla_model

    relation_map = {rel.key: rel for rel in sqla_model.relationships}

    req_cols = []
    for tree_field in fields:
        field_name = tree_field["name"]

        if field_name in relation_map.keys():
            relation = relation_map[field_name]

            for local_col, _ in relation.local_remote_pairs:
                req_cols.append(getattr(selectable.c, local_col.key))
    return req_cols


def get_scalar_columns(tree, selectable):
    """Look ahead in the tree and return a list of columns that need to be in the
    current query so they are available for joining in lower queries"""
    fields = unnest_maybe_nested_fields(tree)
    return_type = tree["return_type"]
    sqla_model = return_type.sqla_model

    column_keys = {x.key for x in sqla_model.columns}

    req_cols = []
    for tree_field in fields:
        field_name = tree_field["name"]
        field_alias = tree_field["alias"]

        if field_name in column_keys:
            req_cols.append(getattr(selectable.c, field_name).label(field_alias))
    return req_cols


def collect_required_columns(tree, selectable):
    cols = get_join_columns(tree, selectable) + get_scalar_columns(tree, selectable)
    # De-duplicate list
    seen = set()
    return_cols = []
    for col in cols:
        if col.key not in seen:
            seen.add(col.key)
            return_cols.append(col)
    return return_cols


def get_info_fields_requiring_subqueries(tree):
    fields = tree["fields"]
    return_type = tree["return_type"]
    sqla_model = return_type.sqla_model
    relation_keys = {rel.key for rel in sqla_model.relationships}

    subquery_fields = []
    for tree_field in fields:
        field_name = tree_field["name"]

        if field_name in relation_keys:
            subquery_fields.append(tree_field)
    return subquery_fields


import typing


def get_where_appender(relation, local: "selectable"):
    def apply_remote_side(remote: "selectable") -> typing.List["whereclause"]:
        clause_builder = []
        for local_col, remote_col in relation.local_remote_pairs:
            clause_builder.append(
                getattr(local.c, local_col.name) == getattr(remote.c, remote_col.name)
            )
        return clause_builder

    return apply_remote_side


def get_field_named(tree, field_name, default=None) -> typing.Optional[typing.Dict]:
    field_arr = [x for x in tree["fields"] if x["name"] == field_name]
    if len(field_arr) == 0:
        return default
    return field_arr[0]


def build_field(field, cte: "selectable", sqla_model) -> "json_sql_expression":

    return_type = field["return_type"]
    field_name = field["name"]

    from ..alias import EdgeType, ObjectType, ScalarType, TableType
    from ..convert.cursor import Cursor
    from ..convert.node_interface import NodeID
    from ..convert.page_info import PageInfo

    if isinstance(return_type, TableType):  # field_name == "node":
        subfield_json_content = func.jsonb_build_object()
        for subfield in field["fields"]:
            json_subfield = build_field(subfield, cte, sqla_model)
            subfield_json_content = subfield_json_content.op("||")(json_subfield)
        return func.jsonb_build_object(literal(field["alias"]), subfield_json_content)

    if isinstance(return_type, ScalarType):
        return func.jsonb_build_object(
            literal(field["alias"]), getattr(cte.c, field["name"])
        )
    print(field_name)

    if isinstance(return_type, ConnectionType):

        subquery_json_content = func.jsonb_build_object()

        for subquery_field in field["fields"]:
            relation_attribute = getattr(sqla_model, field_name)
            relation = relation_attribute.property
            join_callable = get_where_appender(relation, cte)
            standard_query = build_standard_query(
                tree=subquery_field, join_callable=join_callable
            )

            # nodes, edges, pageinfo, totalcount
            subquery_field_name = subquery_field["name"]
            if subquery_field_name == "nodes":
                json_subquery = build_json_query(
                    tree=subquery_field, standard_query=standard_query
                )
                subquery_json_content = subquery_json_content.op("||")(json_subquery)

            elif subquery_field_name == "edges":
                json_subquery = build_json_query(
                    tree=subquery_field, standard_query=standard_query
                )
                subquery_json_content = subquery_json_content.op("||")(json_subquery)
            else:
                # handle pageinfo etc
                raise NotImplementedError(f"on type {return_type}")

        return func.jsonb_build_object(literal(field["alias"]), subquery_json_content)

    raise NotImplementedError(f"on type {return_type}, {field_name}")


def build_standard_query(tree, join_callable: "callable" = None):
    return_type = tree["return_type"]
    sqla_model = return_type.sqla_model
    sqla_table = sqla_model.__table__
    source = sqla_table.alias()
    from sqlalchemy import tuple_

    standard_query = select(source.c + [tuple_(source.c.id).label("cursor")])
    if join_callable is not None:
        for w_clause in join_callable(source):
            standard_query.append_whereclause(w_clause)

    standard_query = standard_query.cte(random_string())
    return standard_query


def build_json_selector(tree, standard_query) -> "non-selected-json-expression":
    sqla_model = tree["return_type"].sqla_model
    sql_json_content = func.jsonb_build_object()

    fields = tree["fields"]
    for field in fields:
        sql_json_field = build_field(field, cte=standard_query, sqla_model=sqla_model)
        sql_json_content = sql_json_content.op("||")(sql_json_field)
    return sql_json_content


def build_json_query(tree, standard_query):
    """Queries are broken down into 2 steps. First we collect the keys
    in a standard query, and then sele"""
    return_alias = tree["alias"]
    return_list = tree["is_list"]

    sql_json_content = build_json_selector(tree, standard_query)
    return select(
        [
            func.jsonb_build_object(
                literal(return_alias),
                func.jsonb_agg(sql_json_content) if return_list else sql_json_content,
            )
        ]
    ).select_from(standard_query)


def build_query_fail(
    tree, join_callable: "callable" = None
):  # , source: "Selector" = None):
    """Queries are broken down into 2 steps. First we collect the keys
    in a standard query, and then sele"""

    return_alias = tree["alias"]

    return_type = tree["return_type"]
    return_list = tree["is_list"]
    sqla_model = return_type.sqla_model
    sqla_table = sqla_model.__table__

    # What are we selecting from?
    # source = source or sqla_table.alias()
    source = sqla_table.alias()

    # Build Filters
    # TODO(OR): Apply the filters

    # standard_query = select(req_cols)
    standard_query = select(source.c)
    if join_callable is not None:
        for w_clause in join_callable(source):
            standard_query.append_whereclause(w_clause)
    standard_query = standard_query.cte(random_string())

    # Build JSON Fields Excluding Any That Require a subquery
    # Return all fields as scalars
    sql_json_content = func.jsonb_build_object()

    fields = tree["fields"]
    for field in fields:
        sql_json_field = build_field(field, cte=standard_query, sqla_model=sqla_model)
        sql_json_content = sql_json_content.op("||")(sql_json_field)

    return select(
        [
            func.jsonb_build_object(
                literal(return_alias),
                func.jsonb_agg(sql_json_content) if return_list else sql_json_content,
            )
        ]
    ).select_from(
        standard_query
    )  # .alias(random_string())


def resolver(_, info: ResolveInfo, **kwargs):
    context = info.context
    session = context["session"]

    return_type = info.return_type
    sqla_model = return_type.sqla_model
    tree = parse_resolve_info(info)
    # print(json.dumps(tree, indent=2, cls=Encoder))

    node_model_name, node_model_id = tree["args"]["nodeId"]
    assert sqla_model.__table__.name == node_model_name

    # Apply node argument
    sqla_table = sqla_model.__table__

    top_alias = sqla_table.alias()

    # Apply argument filters
    # Argument is not optional in this case
    node_alias = tree["alias"]

    query = (
        select(
            [
                func.json_build_object(
                    literal(node_alias), resolve_one(tree=tree, parent_query=top_alias)
                )
            ]
        )
        .where(top_alias.c.id == node_model_id)
        .alias()
    )

    print_query(query)

    result = session.query(query).all()
    print_json(result)
    result = result[0][0]
    context["result"] = result

    return result


import string
import random


def random_string(length=8):
    letters = string.ascii_lowercase
    return "".join(random.choices(letters, k=length))
