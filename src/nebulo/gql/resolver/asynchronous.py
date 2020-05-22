from __future__ import annotations

import asyncio
import json
import typing

from nebulo.config import Config
from nebulo.gql.alias import (
    CompositeType,
    ConnectionType,
    CreatePayloadType,
    UpdatePayloadType,
    ObjectType,
    ResolveInfo,
    ScalarType,
    TableType,
)
from nebulo.gql.mutation_builder import build_insert, build_update
from nebulo.gql.parse_info import parse_resolve_info
from nebulo.gql.query_builder import sql_builder, sql_finalize
from nebulo.gql.relay.node_interface import from_global_id, to_global_id
from nebulo.sql.inspect import get_table_name


from sqlalchemy import create_engine
dial_eng = create_engine('postgresql://')

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
            #claim_coroutine = database.execute(claim_sql)
            #coroutines.append(claim_coroutine)

        if coroutines:
            pass
            #await asyncio.wait(coroutines)

        if isinstance(tree.return_type, CreatePayloadType):
            insert_stmt = build_insert(tree)
            row = await database.fetch_one(query=insert_stmt)

            # Compute nodeId
            sqla_model = tree.return_type.sqla_model
            pkey_values = [x for x in row.values()]
            # base 64 encoded
            node_id = to_global_id(get_table_name(sqla_model), pkey_values)
            # string representation
            global_id = from_global_id(node_id)

            maybe_mutation_id = tree.args['input'].get("clientMutationId")
            output_row_name: str = Config.table_name_mapper(tree.return_type.sqla_model)

            # Retrive the part of the info tree describing the return fields
            # for the current model
            result = {}

            maybe_mut_id = [x for x in tree.fields if x.name == "clientMutationId"]
            if maybe_mut_id:
                mut_id = maybe_mut_id[0]
                result[mut_id.alias] = maybe_mutation_id

            maybe_query_tree = [x for x in tree.fields if x.name == output_row_name]
            if maybe_query_tree:
                query_tree = maybe_query_tree[0]
                query_tree.args["nodeId"] = global_id
                base_query = sql_builder(query_tree)
                query = sql_finalize(query_tree.name, base_query)
                coro_result = await database.fetch_one(query=query)
                str_result: str = coro_result["jsonb_build_object"]
                j_result = json.loads(str_result)
                result.update(j_result)

            result = {tree.alias: result}

        elif isinstance(tree.return_type, UpdatePayloadType):
            global_id = tree.args['nodeId']
            update_stmt = build_update(tree)
            row = await database.fetch_one(query=update_stmt)

            # Compute nodeId
            sqla_model = tree.return_type.sqla_model
            pkey_values = [x for x in row.values()]
            # base 64 encoded
            node_id = to_global_id(get_table_name(sqla_model), pkey_values)
            # string representation
            global_id = from_global_id(node_id)

            maybe_mutation_id = tree.args['input'].get("clientMutationId")
            output_row_name: str = Config.table_name_mapper(tree.return_type.sqla_model)

            # Retrive the part of the info tree describing the return fields
            # for the current model
            result = {}

            maybe_mut_id = [x for x in tree.fields if x.name == "clientMutationId"]
            if maybe_mut_id:
                mut_id = maybe_mut_id[0]
                result[mut_id.alias] = maybe_mutation_id

            maybe_query_tree = [x for x in tree.fields if x.name == output_row_name]
            if maybe_query_tree:
                query_tree = maybe_query_tree[0]
                query_tree.args["nodeId"] = global_id
                base_query = sql_builder(query_tree)
                query = sql_finalize(query_tree.name, base_query)
                coro_result = await database.fetch_one(query=query)
                str_result: str = coro_result["jsonb_build_object"]
                j_result = json.loads(str_result)
                result.update(j_result)

            result = {tree.alias: result}


        elif isinstance(tree.return_type, ObjectType):
            base_query = sql_builder(tree)
            query = sql_finalize(tree.name, base_query)
            query =  str(query.compile(compile_kwargs={'literal_binds': True, 'engine': dial_eng}))
            print(query)
            query_coro = database.fetch_one(query=query)
            coro_result = await query_coro
            str_result: str = coro_result["json"]
            result = json.loads(str_result)
        elif isinstance(tree.return_type, ScalarType):
            base_query = sql_builder(tree)
            query = base_query
            query_coro = database.fetch_one(query=query)
            scalar_result = await query_coro
            result = next(scalar_result._row.values())  # pylint: disable=protected-access

        else:
            raise Exception("sql builder could not handle return type")
    #print(json.dumps(result, indent=2))
    # Stash result on context to enable dumb resolvers to not fail
    context["result"] = result
    return result
