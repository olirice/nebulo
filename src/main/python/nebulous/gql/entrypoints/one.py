from ..alias import Argument, Field, ResolveInfo
from ..convert.node_interface import NodeID
from ..convert.table import table_factory
from ..parse_info import parse_resolve_info
from .sql_builder import sql_builder, sql_finalize


def one_node_factory(sqla_model) -> Field:
    node = table_factory(sqla_model)
    return Field(node, args={"nodeId": Argument(NodeID)}, resolver=resolver, description="")


def resolver(_, info: ResolveInfo, **kwargs):
    context = info.context
    session = context["session"]

    tree = parse_resolve_info(info)
    query = sql_finalize(tree["name"], sql_builder(tree))
    result = session.execute(query).fetchone()[0]

    print(query)
    print(result)

    # Stash result on context to enable dumb resolvers to not fail
    context["result"] = result
    return result
