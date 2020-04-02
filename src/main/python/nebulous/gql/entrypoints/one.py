import json

from sqlalchemy import func, select
from sqlalchemy.sql.expression import literal

from ..alias import Argument, Field, ResolveInfo
from ..convert.node_interface import NodeID
from ..convert.sql_resolver import resolve_one
from ..convert.table import table_factory
from ..parse_info import parse_resolve_info


class Encoder(json.JSONEncoder):
    def default(self, o):
        return str(o)


def one_node_factory(sqla_model) -> Field:
    node = table_factory(sqla_model)
    return Field(node, args={"NodeID": Argument(NodeID)}, resolver=resolver, description="")


def resolver(_, info: ResolveInfo, **kwargs):
    context = info.context
    session = context["session"]

    return_type = info.return_type
    sqla_model = return_type.sqla_model
    tree = parse_resolve_info(info)
    # print(json.dumps(tree, indent=2, cls=Encoder))

    node_model_name, node_model_id = tree["args"]["NodeID"]
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

    # import sqlparse
    # query_str = query.compile(compile_kwargs={"literal_binds": True})
    # query_str = str(query_str)
    # print(sqlparse.format(query_str, reindent=True, keyword_case="upper"))

    result = session.query(query).all()
    result = result[0][0]
    context["result"] = result

    # Stash result on context so enable dumb resolvers to not fail
    # pretty_result = json.dumps(result, indent=2, cls=Encoder)
    # print(pretty_result)

    return result
