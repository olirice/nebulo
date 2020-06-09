from __future__ import annotations

import json
import typing

from nebulo.config import Config
from nebulo.gql.alias import (
    CompositeType,
    ConnectionType,
    CreatePayloadType,
    MutationPayloadType,
    ObjectType,
    ResolveInfo,
    ScalarType,
    TableType,
    UpdatePayloadType,
)
from nebulo.gql.mutation_builder import build_insert, build_update
from nebulo.gql.parse_info import parse_resolve_info
from nebulo.gql.query_builder import sql_builder, sql_finalize
from nebulo.gql.relay.node_interface import NodeIdStructure


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
            # claim_coroutine = database.execute(claim_sql)
            # coroutines.append(claim_coroutine)

        if coroutines:
            # await asyncio.wait(coroutines)
            pass

        if isinstance(tree.return_type, MutationPayloadType):
            stmt = build_insert(tree) if isinstance(tree.return_type, CreatePayloadType) else build_update(tree)

            row = json.loads((await database.fetch_one(query=stmt))["nodeId"])
            node_id = NodeIdStructure.from_dict(row)

            maybe_mutation_id = tree.args["input"].get("clientMutationId")
            mutation_id_alias = next(
                iter([x.alias for x in tree.fields if x.name == "clientMutationId"]), "clientMutationId"
            )
            node_id_alias = next(iter([x.alias for x in tree.fields if x.name == "nodeId"]), "nodeId")
            output_row_name: str = Config.table_name_mapper(tree.return_type.sqla_model)
            result = {tree.alias: {mutation_id_alias: maybe_mutation_id}, node_id_alias: node_id}
            query_tree = next(iter([x for x in tree.fields if x.name == output_row_name]), None)
            if query_tree:
                # Set the nodeid of the newly created record as an arg
                query_tree.args["nodeId"] = node_id
                base_query = sql_builder(query_tree)
                query = sql_finalize(query_tree.name, base_query)
                coro_result: str = (await database.fetch_one(query=query))["json"]
                sql_result = json.loads(coro_result)
                result[tree.alias].update(sql_result)

        elif isinstance(tree.return_type, ObjectType):
            base_query = sql_builder(tree)
            # print(base_query)
            query = sql_finalize(tree.name, base_query)

            # from sqlalchemy import create_engine
            # dial_eng = create_engine("postgresql://")
            # query = str(query.compile(compile_kwargs={"literal_binds": True, "engine": dial_eng}))
            # print(query)
            query_coro = database.fetch_one(query=query)
            coro_result = await query_coro
            str_result: str = coro_result["json"]
            result = json.loads(str_result)
            # print(result)
        elif isinstance(tree.return_type, ScalarType):
            base_query = sql_builder(tree)
            query = base_query
            query_coro = database.fetch_one(query=query)
            scalar_result = await query_coro
            result = next(scalar_result._row.values())  # pylint: disable=protected-access

        else:
            raise Exception("sql builder could not handle return type")

    # Stash result on context to enable dumb resolvers to not fail
    # print(json.dumps(result))
    context["result"] = result
    return result
