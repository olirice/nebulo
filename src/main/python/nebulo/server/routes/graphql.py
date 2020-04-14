from graphql import graphql as graphql_exec
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


async def get_query(request):
    content_type = request.headers.get("content-type", "")
    if content_type == "application/graphql":
        return await request.body()
    if content_type == "application/json":
        return (await request.json())["query"]
    raise HTTPException(400, "content-type header must be set")


async def get_variables(request):
    content_type = request.headers.get("content-type", "")
    if content_type == "application/graphql":
        raise NotImplementedError("Getting variables from graphql content type not known")

    if content_type == "application/json":
        return (await request.json()).get("variables", {})
    raise HTTPException(400, "content-type header must be set")


def get_graphql_endpoint(schema, database):
    async def graphql_endpoint(request):
        query = await get_query(request)
        variables = await get_variables(request)
        request_context = {"request": request, "database": database, "query": query, "variables": variables}
        result = await graphql_exec(
            schema=schema, source=query, context_value=request_context, variable_values=variables
        )
        errors = result.errors
        result_dict = {"data": result.data, "errors": [error.formatted for error in errors or []]}
        return JSONResponse(result_dict)

    return graphql_endpoint
