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


def print_query(query):
    import sqlparse

    compiled_query = query.compile(compile_kwargs={"literal_binds": True})
    print(sqlparse.format(str(compiled_query), reindent=True, keyword_case="upper"))
    return


def print_result(result):
    pretty_result = json.dumps(result, indent=2, cls=Encoder)
    print(pretty_result)


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

    print_query(query)

    result = session.query(query).all()
    print_result(result)
    result = result[0][0]
    context["result"] = result

    # Stash result on context so enable dumb resolvers to not fail
    # pretty_result = json.dumps(result, indent=2, cls=Encoder)
    # print(pretty_result)

    return result


def cte_resolver(_, info: ResolveInfo, **kwargs):
    context = info.context
    session = context["session"]

    return_type = info.return_type
    sqla_model = return_type.sqla_model
    tree = parse_resolve_info(info)
    print(tree)

    field_alias = tree["alias"]
    query = build_query(field_alias, tree, None)

    print_query(query)

    compiled_query = query.compile(compile_kwargs={"literal_binds": False})
    bind_params = compiled_query.params
    result = session.execute(query, bind_params).fetchone()

    print_result(result)

    # Stash result on context so enable dumb resolvers to not fail
    context["result"] = result
    return result


def build_query(field_alias: str, tree, source: "Selector" = None):
    from ..convert.sql_resolver import relationship_to_attr_name

    # Parent_source must have a '.c' field

    return_alias = tree["alias"]

    return_type = tree["return_type"]
    sqla_model = return_type.sqla_model
    sqla_table = sqla_model.__table__

    # What are we selecting from?
    source = source or sqla_table.alias()

    # Maps graphql model attribute to sqla relationship
    relation_map = {relationship_to_attr_name(rel): rel for rel in sqla_model.relationships}

    query = select([])

    builder = []

    for field in tree["fields"]:
        print("Field", field)
        field_name = field["name"]
        field_alias = field["alias"]

        # Standard column resolver
        query.append_column(source.columns[field_name].label(field_alias))
        # builder.extend(literal(field_alias),)

    # node_model_name, node_model_id = tree["args"]["NodeID"]
    # assert sqla_model.__table__.name == node_model_name

    # query = select([
    #    func.json_build_object([
    #        *builder
    #    ])
    # ])

    return query
