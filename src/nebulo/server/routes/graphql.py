from typing import Any, Awaitable, Callable, Dict

import jwt
from databases import Database
from graphql import graphql as graphql_exec
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

__all__ = ["get_graphql_endpoint"]


def get_graphql_endpoint(
    schema: str, database: Database, jwt_secret: str
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


def get_jwt_claims_handler(secret: str) -> Callable[[Request], Awaitable[Dict[str, Any]]]:
    """Return a function that retrieves and decodes JWT claims from the Starlette Request"""

    async def get_jwt_claims(request: Request) -> Dict[str, Any]:
        """Retrieve the JWT claims from the Starlette Request"""

        if "Authorization" not in request.headers:
            return {}

        auth = request.headers["Authorization"]
        try:
            scheme, token = auth.split()
            if scheme.lower() == "bearer":
                contents = jwt.decode(token, secret, algorithms=["HS256"])
                return contents
        except (jwt.exceptions.DecodeError,):  # type: ignore
            raise HTTPException(401, "Invalid JWT credentials")
        return {}

    return get_jwt_claims
