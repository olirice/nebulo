import json

from nebulo.gql.alias import ResolveInfo
from nebulo.gql.entrypoints.sql_builder import sql_builder, sql_finalize
from nebulo.gql.parse_info import parse_resolve_info


def sync_resolver(_, info: ResolveInfo, **kwargs):
    """GraphQL Entrypoint resolver

    Expects:
        info.context['session'] to contain a sqlalchemy.orm.Session
    """

    context = info.context
    session = context["session"]
    tree = parse_resolve_info(info)
    query = sql_finalize(tree.name, sql_builder(tree))
    result = session.execute(query).fetchone()[0]
    # Stash result on context to enable dumb resolvers to not fail
    context["result"] = result
    return result


async def async_resolver(_, info: ResolveInfo, **kwargs):
    """Awaitable GraphQL Entrypoint resolver

    Expects:
        info.context['database'] to contain a databases.Database
    """
    context = info.context
    database = context["database"]
    tree = parse_resolve_info(info)
    query: str = sql_finalize(tree.name, sql_builder(tree))
    str_result: str = (await database.fetch_one(query=query))["jsonb_build_object"]
    result = json.loads(str_result)
    # Stash result on context to enable dumb resolvers to not fail
    context["result"] = result
    return result
