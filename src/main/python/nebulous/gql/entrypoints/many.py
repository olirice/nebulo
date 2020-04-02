from ..alias import Field
from ..convert.connection import connection_args_factory, connection_factory
from .resolver import resolver


def many_node_factory(sqla_model) -> Field:
    connection = connection_factory(sqla_model)
    return Field(
        connection, args=connection_args_factory(sqla_model), resolver=resolver, description=""
    )
