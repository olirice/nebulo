from sqlalchemy import func, select
from sqlalchemy.sql.expression import literal, literal_column

from ..alias import Argument, Field, ResolveInfo, ConnectionType
from ..convert.node_interface import NodeID
from ..convert.sql_resolver import resolve_one
from ..convert.table import table_factory
from ..parse_info import parse_resolve_info
from .utils import print_json, print_query
import typing

from ..alias import EdgeType, ObjectType, ScalarType, TableType, ConnectionType
from ..convert.cursor import Cursor
from ..convert.node_interface import NodeID
from ..convert.page_info import PageInfo
import string
import random

from .sql_builder import sql_builder, sql_finalize



def one_node_factory(sqla_model) -> Field:
    node = table_factory(sqla_model)
    return Field(
        node, args={"nodeId": Argument(NodeID)}, resolver=resolver, description=""
    )


def resolver(_, info: ResolveInfo, **kwargs):
    context = info.context
    session = context["session"]

    tree = parse_resolve_info(info)
    # print(tree)

    # standard_query = build_standard_query(tree, None)
    # query = build_json_query(tree, standard_query)
    query = sql_finalize(tree["name"], sql_builder(tree))
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


