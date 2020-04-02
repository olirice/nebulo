from nebulo.gql.alias import ResolveInfo
from nebulo.gql.entrypoints.sql_builder import sql_builder, sql_finalize
from nebulo.gql.parse_info import parse_resolve_info


def resolver(_, info: ResolveInfo, **kwargs):
    context = info.context
    session = context["session"]

    tree = parse_resolve_info(info)
    query = sql_finalize(tree.name, sql_builder(tree))
    result = session.execute(query).fetchone()[0]

    # print(query)
    # print(json.dumps(result, indent=2))

    # Stash result on context to enable dumb resolvers to not fail
    context["result"] = result
    return result
