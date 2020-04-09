from starlette.responses import JSONResponse


async def http_exception(request, exc):  # pylint: disable=unused-argument
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
