from sqlalchemy import func, select
from sqlalchemy.sql.expression import literal, literal_column

from ..alias import Argument, Field, ResolveInfo, ConnectionType
from ..convert.node_interface import NodeID
from ..convert.sql_resolver import resolve_one
from ..convert.table import table_factory
from ..parse_info import parse_resolve_info
from .utils import print_json, print_query


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

    query = build_query(tree, None)

    print_query(query)

    compiled_query = query.compile(compile_kwargs={"literal_binds": False})
    bind_params = compiled_query.params
    result = session.execute(query, bind_params).fetchone()[0]

    print_json(result)

    # Stash result on context so enable dumb resolvers to not fail
    context["result"] = result
    return result


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

    from ..alias import EdgeType, ObjectType, ScalarType
    from ..convert.cursor import Cursor
    from ..convert.node_interface import NodeID
    from ..convert.page_info import PageInfo

    if isinstance(return_type, ScalarType):
        return func.jsonb_build_object(
            literal(field["alias"]), getattr(cte.c, field["name"])
        )

    if isinstance(return_type, ConnectionType):

        subquery_json_content = func.jsonb_build_object()

        for subquery_field in field["fields"]:
            # nodes, edges, pageinfo, totalcount
            subquery_field_name = subquery_field["name"]
            if subquery_field_name in ("nodes", "edges"):
                relation_attribute = getattr(sqla_model, field_name)
                relation = relation_attribute.property
                join_callable = get_where_appender(relation, cte)
                json_subquery = build_query(
                    tree=subquery_field, join_callable=join_callable
                )
                subquery_json_content = subquery_json_content.op("||")(json_subquery)
            else:
                # handle pageinfo etc
                raise NotImplementedError(f"on type {return_type}")

        return func.jsonb_build_object(literal(field["alias"]), subquery_json_content)

    raise NotImplementedError(f"on type {return_type}")

    if isinstance(return_type, ObjectType):
        builder = []
        for field in tree["fields"]:
            builder.append(literal(field["alias"]), field_to_selector(field, cte))

    if isinstance(return_type, Cursor):
        raise NotImplementedError()

    if isinstance(return_type, NodeID):
        raise NotImplementedError()

    builder = []
    nodes_field = get_field_named(tree, "nodes")
    if nodes_field is not None:
        # build_nodes(nodes_field, cte)
        pass


def build_query(
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

    # TODO(OR): Add nodeId, cursor, pageInfo to this etc
    # req_cols = collect_required_columns(tree, source)

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
