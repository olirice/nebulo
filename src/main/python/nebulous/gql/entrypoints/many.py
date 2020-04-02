from nebulous.gql.alias import Field
from nebulous.gql.convert.connection import connection_args_factory, connection_factory
from nebulous.gql.entrypoints.resolver import resolver


def many_node_factory(sqla_model) -> Field:
    connection = connection_factory(sqla_model)
    return Field(
        connection, args=connection_args_factory(sqla_model), resolver=resolver, description=""
    )
