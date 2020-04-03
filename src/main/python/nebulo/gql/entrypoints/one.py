from nebulo.gql.alias import Argument, Field, NonNull
from nebulo.gql.convert.node_interface import NodeID
from nebulo.gql.convert.table import table_factory
from nebulo.gql.entrypoints.resolver import resolver


def one_node_factory(sqla_model) -> Field:
    node = table_factory(sqla_model)
    return Field(node, args={"nodeId": Argument(NonNull(NodeID))}, resolver=resolver, description="")
