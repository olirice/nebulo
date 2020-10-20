from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse


async def http_exception(request: Request, exc: HTTPException):
    """Starlette exception handler converting starlette.exceptions.HTTPException into GraphQL responses"""
    return JSONResponse({"data": None, "errors": [exc.detail]}, status_code=exc.status_code)
