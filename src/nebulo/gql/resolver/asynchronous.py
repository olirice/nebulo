from __future__ import annotations

import asyncio
import json
import typing

from nebulo.gql.alias import (
    CompositeType,
    ConnectionType,
    CreatePayloadType,
    ObjectType,
    ResolveInfo,
    ScalarType,
    TableType,
)
from nebulo.gql.insert_builder import build_insert, row_to_create_result
from nebulo.gql.parse_info import parse_resolve_info
from nebulo.gql.query_builder import sql_builder, sql_finalize


async def async_resolver(_, info: ResolveInfo, **kwargs) -> typing.Any:
    """Awaitable GraphQL Entrypoint resolver

    Expects:
        info.context['database'] to contain a databases.Database
    """
    context = info.context
    database = context["database"]
    jwt_claims = context["jwt_claims"]
    tree = parse_resolve_info(info)

    async with database.transaction():
        # GraphQL automatically resolves the top level object name
        # At time of writing, only required for scalar functions

        # TODO(OR): Can't get databases to execute these as prepared statements
        coroutines = []
        for claim_key, claim_value in jwt_claims.items():
            claim_sql = f"set local jwt.claims.{claim_key} to {claim_value};"
            claim_coroutine = database.execute(claim_sql)
            coroutines.append(claim_coroutine)

        if coroutines:
            await asyncio.wait(coroutines)

        if isinstance(tree.return_type, CreatePayloadType):
            insert_stmt = build_insert(tree)
            row = await database.fetch_one(query=insert_stmt)
            result = row_to_create_result(tree, row)

        elif isinstance(tree.return_type, ObjectType):
            base_query = sql_builder(tree)
            query = sql_finalize(tree.name, base_query)
            query_coro = database.fetch_one(query=query)
            coro_result = await query_coro
            str_result: str = coro_result["jsonb_build_object"]
            result = json.loads(str_result)
        elif isinstance(tree.return_type, ScalarType):
            base_query = sql_builder(tree)
            query = base_query
            query_coro = database.fetch_one(query=query)
            scalar_result = await query_coro
            result = next(scalar_result._row.values())  # pylint: disable=protected-access

        else:
            raise Exception("sql builder could not handle return type")

    # Stash result on context to enable dumb resolvers to not fail
    context["result"] = result
    return result
