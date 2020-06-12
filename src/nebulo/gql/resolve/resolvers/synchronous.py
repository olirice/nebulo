from __future__ import annotations

import typing

from nebulo.gql.alias import ObjectType, ResolveInfo, ScalarType
from nebulo.gql.parse_info import parse_resolve_info
from nebulo.gql.resolve.transpile.query_builder import sql_builder, sql_finalize


def sync_resolver(_, info: ResolveInfo, **kwargs) -> typing.Any:
    """GraphQL Entrypoint resolver

    Expects:
        info.context['session'] to contain a sqlalchemy.orm.Session
    """

    context = info.context
    session = context["session"]
    jwt_claims = context["jwt_claims"]
    tree = parse_resolve_info(info)
    base_query = sql_builder(tree)

    # GraphQL automatically resolves the top level object name
    # At time of writing, only required for scalar functions
    local_params = [
        {"claim_key": "jwt.claims." + claim_key, "claim_value": claim_value}
        for claim_key, claim_value in jwt_claims.items()
    ]
    if local_params:
        session.execute_many("set local :claim_key to :claim_value", values=local_params)

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
