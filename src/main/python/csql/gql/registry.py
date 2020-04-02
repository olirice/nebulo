class Registry:
    """Registry of converters for converting sqlalchemy models
    into graphql components"""

    model_name_to_sqla = {}

    sqla_to_model = {}
    sqla_to_condition = {}
    sqla_to_connection = {}
    sqla_to_edge = {}
    sqla_to_order_by = {}
    # sqla_to_gql_input = {}
    # sqla_to_gql_patch = {}


def get_registry() -> Registry:
    """Retrieve an instance of the global converter registry"""
    return Registry
