from sqlalchemy import func, select
from sqlalchemy.sql.expression import literal

from ..alias import Field, ResolveInfo
from ..convert.connection import connection_args_factory, connection_factory, resolve_connection
from ..parse_info import parse_resolve_info
from .utils import print_json, print_query


def many_node_factory(sqla_model) -> Field:
    name = "all_" + sqla_model.__table__.name
    connection = connection_factory(sqla_model)
    return Field(
        connection, args=connection_args_factory(sqla_model), resolver=resolver, description=""
    )


def resolver(obj, info: ResolveInfo, **kwargs):
    context = info.context
    session = context["session"]

    return_type = info.return_type
    sqla_model = return_type.sqla_model
    tree = parse_resolve_info(info)
    # print(json.dumps(tree, indent=2, cls=Encoder))

    # Apply node argument
    sqla_table = sqla_model.__table__

    top_alias = select([sqla_table]).alias()

    # Apply argument filters
    # Argument is not optional in this case
    node_alias = tree["alias"]

    select_clause = resolve_connection(tree, parent_query=top_alias)

    # Apply filters, limits, arguments etc... I don't like it either.
    selector = select([func.json_build_object(literal(node_alias), select_clause)])

    query = selector.alias()

    print_query(query)

    result = session.query(query).all()
    print_json(result)
    result = result[0][0]
    context["result"] = result

    return result
