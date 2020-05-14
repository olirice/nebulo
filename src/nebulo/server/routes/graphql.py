from typing import Any, Awaitable, Callable, Dict, Optional

from databases import Database
from graphql import graphql as graphql_exec
from nebulo.server.jwt import get_jwt_claims_handler
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

__all__ = ["get_graphql_endpoint"]


def get_graphql_endpoint(
    schema: str, database: Database, jwt_secret: Optional[str]
) -> Callable[[Request], Awaitable[JSONResponse]]:
    """Retrieve the GraphQL variables from the Starlette Request"""

    get_jwt_claims = get_jwt_claims_handler(jwt_secret)

    async def graphql_endpoint(request):

        query = await get_query(request)
        variables = await get_variables(request)
        jwt_claims = await get_jwt_claims(request)
        request_context = {
            "request": request,
            "database": database,
            "query": query,
            "variables": variables,
            "jwt_claims": jwt_claims,
        }
        result = await graphql_exec(
            schema=schema, source=query, context_value=request_context, variable_values=variables
        )
        errors = result.errors
        result_dict = {"data": result.data, "errors": [error.formatted for error in errors or []]}
        return JSONResponse(result_dict)

    return graphql_endpoint


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
