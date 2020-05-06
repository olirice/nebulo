from __future__ import annotations

import json

from nebulo.gql.alias import ObjectType, ResolveInfo, ScalarType
from nebulo.gql.parse_info import parse_resolve_info
from nebulo.gql.query_builder import sql_builder, sql_finalize


def sync_resolver(_, info: ResolveInfo, **kwargs):
    """GraphQL Entrypoint resolver

    Expects:
        info.context['session'] to contain a sqlalchemy.orm.Session
    """

    context = info.context
    session = context["session"]
    tree = parse_resolve_info(info)
    base_query = sql_builder(tree)

    # GraphQL automatically resolves the top level object name
    # At time of writing, only required for scalar functions
    if isinstance(tree.return_type, ObjectType):
        query = sql_finalize(tree.name, base_query)
        result = session.execute(query).fetchone()[0]
    elif isinstance(tree.return_type, ScalarType):
        result = session.execute(base_query).fetchone()[0]
    else:
        raise Exception("sql builder could not handle return type")

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
    base_query = sql_builder(tree)

    # GraphQL automatically resolves the top level object name
    # At time of writing, only required for scalar functions
    if isinstance(tree.return_type, ObjectType):
        query = sql_finalize(tree.name, base_query)
        str_result: str = (await database.fetch_one(query=query))["jsonb_build_object"]
        result = json.loads(str_result)
    elif isinstance(tree.return_type, ScalarType):
        scalar_result = await database.fetch_one(query=base_query)
        result = next(scalar_result._row.values())  # pylint: disable=protected-access
    else:
        raise Exception("sql builder could not handle return type")

    # Stash result on context to enable dumb resolvers to not fail
    context["result"] = result
    return result
