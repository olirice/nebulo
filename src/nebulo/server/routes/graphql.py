from typing import Any, Awaitable, Dict, Optional

from databases import Database
from graphql import graphql as graphql_exec
from nebulo.gql.alias import Schema
from nebulo.server.jwt import get_jwt_claims_handler
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

__all__ = ["get_graphql_route"]


def get_graphql_route(
    gql_schema: Schema,
    database: Database,
    path: str = "/",
    jwt_secret: Optional[str] = None,
    default_role: Optional[str] = None,
    name: Optional[str] = None,
) -> Route:
    """Create a Starlette Route to serve GraphQL requests

    **Parameters**

    * **schema**: _Schema_ = A GraphQL-core schema
    * **database**: _Database_ = Database object for communicating with PostgreSQL
    * **path**: _str_ = URL path to serve GraphQL from, e.g. '/'
    * **jwt_secret**: _str_ = secret key used to encrypt JWT contents
    * **default_role**: _str_ = Default SQL role to use when serving unauthenticated requests
    * **name**: _str_ = Name of the GraphQL serving Starlette route
    """

    get_jwt_claims = get_jwt_claims_handler(jwt_secret)

    async def graphql_endpoint(request: Request) -> Awaitable[JSONResponse]:

        query = await get_query(request)
        variables = await get_variables(request)
        jwt_claims = await get_jwt_claims(request)
        request_context = {
            "request": request,
            "database": database,
            "query": query,
            "variables": variables,
            "jwt_claims": jwt_claims,
            "default_role": default_role,
        }
        result = await graphql_exec(
            schema=gql_schema,
            source=query,
            context_value=request_context,
            variable_values=variables,
        )
        errors = result.errors
        result_dict = {
            "data": result.data,
            "errors": [error.formatted for error in errors or []],
        }
        return JSONResponse(result_dict)

    graphql_route = Route(path=path, endpoint=graphql_endpoint, methods=["POST"], name=name)

    return graphql_route


async def get_query(request: Request) -> Awaitable[str]:
    """Retrieve the GraphQL query from the Starlette Request"""

    content_type = request.headers.get("content-type", "")
    if content_type == "application/graphql":
        return await request.body()
    if content_type == "application/json":
        return (await request.json())["query"]
    raise HTTPException(400, "content-type header must be set")


async def get_variables(request) -> Awaitable[Dict[str, Any]]:
    """Retrieve the GraphQL variables from the Starlette Request"""

    content_type = request.headers.get("content-type", "")
    if content_type == "application/graphql":
        raise NotImplementedError("Getting variables from graphql content type not known")

    if content_type == "application/json":
        return (await request.json()).get("variables", {})
    raise HTTPException(400, "content-type header must be set")
