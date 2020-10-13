from __future__ import annotations

import json
import typing

from flupy import flu
from nebulo.config import Config
from nebulo.gql.alias import (
    CompositeType,
    ConnectionType,
    CreatePayloadType,
    DeletePayloadType,
    FunctionPayloadType,
    MutationPayloadType,
    ObjectType,
    ResolveInfo,
    ScalarType,
    TableType,
    UpdatePayloadType,
)
from nebulo.gql.parse_info import parse_resolve_info
from nebulo.gql.relay.node_interface import NodeIdStructure, to_node_id_sql
from nebulo.gql.resolve.transpile.mutation_builder import build_mutation
from nebulo.gql.resolve.transpile.query_builder import sql_builder, sql_finalize
from nebulo.sql.table_base import TableProtocol
from sqlalchemy import Text, func, literal, select


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

        if jwt_claims:
            # Setting local variables an not be done in prepared statement
            # since JWT claims are signed, literal binds should be ok
            claims = [
                func.set_config(
                    literal("jwt.claims.").op("||")(func.cast(claim_key, Text())),
                    func.cast(str(claim_value), Text()),
                    True,
                )
                for claim_key, claim_value in jwt_claims.items()
            ]
            await database.execute(select(claims))

        result: typing.Dict[str, typing.Any]

        if isinstance(tree.return_type, FunctionPayloadType):
            sql_function = tree.return_type.sql_function
            function_args = [val for key, val in tree.args["input"].items() if key != "clientMutationId"]
            func_call = sql_function.to_executable(function_args)
            stmt = select([func_call.label("result")])

            # Function returning table row
            if isinstance(sql_function.return_sqla_type, TableProtocol):
                return_sqla_model = sql_function.return_sqla_type
                core_table = return_sqla_model.__table__
                stmt = select([to_node_id_sql(return_sqla_model, core_table.alias()).label("nodeId")]).select_from(
                    stmt.alias()
                )
                stmt_result = await database.fetch_one(query=stmt)
                row = json.loads(stmt_result["nodeId"])
                node_id = NodeIdStructure.from_dict(row)

                # Add nodeId to AST and query
                query_tree = next(iter([x for x in tree.fields if x.name == "result"]), None)
                if query_tree is not None:
                    query_tree.args["nodeId"] = node_id
                    base_query = sql_builder(query_tree)
                    query = sql_finalize(query_tree.alias, base_query)
                    coro_rvf_result: str = (await database.fetch_one(query=query))["json"]
                    stmt_result = json.loads(coro_rvf_result)
                else:
                    stmt_result = {}
            else:
                stmt_result = await database.fetch_one(query=stmt)

            maybe_mutation_id = tree.args["input"].get("clientMutationId")
            mutation_id_alias = next(
                iter([x.alias for x in tree.fields if x.name == "clientMutationId"]),
                "clientMutationId",
            )
            result = {tree.alias: {**stmt_result, **{mutation_id_alias: maybe_mutation_id}}}

        elif isinstance(tree.return_type, MutationPayloadType):
            stmt = build_mutation(tree)
            stmt_result = await database.fetch_one(query=stmt)
            row = json.loads(stmt_result["nodeId"])
            node_id = NodeIdStructure.from_dict(row)

            maybe_mutation_id = tree.args["input"].get("clientMutationId")
            mutation_id_alias = next(
                iter([x.alias for x in tree.fields if x.name == "clientMutationId"]),
                "clientMutationId",
            )
            node_id_alias = next(iter([x.alias for x in tree.fields if x.name == "nodeId"]), "nodeId")
            output_row_name: str = Config.table_name_mapper(tree.return_type.sqla_model)
            query_tree = next(iter([x for x in tree.fields if x.name == output_row_name]), None)
            sql_result = {}
            if query_tree:
                # Set the nodeid of the newly created record as an arg
                query_tree.args["nodeId"] = node_id
                base_query = sql_builder(query_tree)
                query = sql_finalize(query_tree.alias, base_query)
                coro_result: str = (await database.fetch_one(query=query))["json"]
                sql_result = json.loads(coro_result)
            result = {
                tree.alias: {**sql_result, mutation_id_alias: maybe_mutation_id},
                mutation_id_alias: maybe_mutation_id,
                node_id_alias: node_id,
            }

        elif isinstance(tree.return_type, (ObjectType, ScalarType)):
            base_query = sql_builder(tree)
            query = sql_finalize(tree.name, base_query)

            query_coro = database.fetch_one(query=query)
            coro_result = await query_coro
            str_result: str = coro_result["json"]  # type: ignore

            query_json_result = json.loads(str_result)

            if isinstance(tree.return_type, ScalarType):
                # If its a scalar, unwrap the top level name
                result = flu(query_json_result.values()).first(None)
            else:
                result = query_json_result

        else:
            raise Exception("sql builder could not handle return type")

    # Stash result on context to enable dumb resolvers to not fail
    context["result"] = result
    return result
