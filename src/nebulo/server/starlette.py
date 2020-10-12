import os
from pathlib import Path
from typing import Callable, List, Optional

from databases import Database
from nebulo.gql.alias import Schema
from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
from nebulo.server.exception import http_exception
from nebulo.server.routes import get_graphql_endpoint, graphiql_endpoint
from nebulo.sql.reflection.manager import reflect_sqla_models
from sqlalchemy import Table, create_engine
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

STATIC_PATH = Path(os.path.abspath(__file__)).parent.parent.resolve() / "static"


def create_app(
    connection: str,
    schema: str = "public",
    jwt_identifier: Optional[str] = None,
    jwt_secret: Optional[str] = None,
    before_start: Optional[Callable[[Schema, List[Table], Database], Schema]] = None,
) -> Starlette:
    """Create an ASGI App"""

    if not (jwt_identifier is not None) == (jwt_secret is not None):
        raise Exception("jwt_token_identifier and jwt_secret must be provided together")

    database = Database(connection)
    # Reflect database to sqla models
    sqla_engine = create_engine(connection)
    sqla_models, sql_functions = reflect_sqla_models(engine=sqla_engine, schema=schema)

    # Convert sqla models to graphql schema
    gql_schema = sqla_models_to_graphql_schema(
        sqla_models,
        sql_functions,
        jwt_identifier=jwt_identifier,
        jwt_secret=jwt_secret,
    )

    if before_start:
        core_tables = [x.__table__ for x in sqla_models]
        gql_schema = before_start(gql_schema, core_tables, database)

    # Build Starlette app
    graphql_endpoint = get_graphql_endpoint(gql_schema, database, jwt_secret)

    routes = [
        Route("/", graphql_endpoint, methods=["POST"]),
        Route("/graphiql", graphiql_endpoint, methods=["GET"]),
        Mount("/static", StaticFiles(directory=STATIC_PATH), name="static"),
    ]

    middleware = [Middleware(CORSMiddleware, allow_origins=["*"])]

    _app = Starlette(
        routes=routes,
        middleware=middleware,
        exception_handlers={HTTPException: http_exception},
        on_startup=[database.connect],
        on_shutdown=[database.disconnect],
    )

    return _app
