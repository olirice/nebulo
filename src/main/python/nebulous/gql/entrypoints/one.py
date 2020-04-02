from nebulous.gql.alias import Argument, Field
from nebulous.gql.convert.node_interface import NodeID
from nebulous.gql.convert.table import table_factory
from nebulous.gql.entrypoints.resolver import resolver


def one_node_factory(sqla_model) -> Field:
    node = table_factory(sqla_model)
    return Field(node, args={"nodeId": Argument(NodeID)}, resolver=resolver, description="")
