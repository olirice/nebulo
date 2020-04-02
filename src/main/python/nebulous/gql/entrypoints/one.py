from ..alias import Argument, Field
from ..convert.node_interface import NodeID
from ..convert.table import table_factory
from .resolver import resolver


def one_node_factory(sqla_model) -> Field:
    node = table_factory(sqla_model)
    return Field(node, args={"nodeId": Argument(NodeID)}, resolver=resolver, description="")
