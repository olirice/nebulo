from typing import Optional

from databases import Database
from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
from nebulo.server.exception import http_exception
from nebulo.server.routes import get_graphiql_route, get_graphql_route
from nebulo.sql.reflection.manager import reflect_sqla_models
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware


def create_app(
    connection: str,
    schema: str = "public",
    jwt_identifier: Optional[str] = None,
    jwt_secret: Optional[str] = None,
    default_role: Optional[str] = None,
) -> Starlette:
    """Instantiate the Starlette app"""

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

    graphql_path = "/"

    graphql_route = get_graphql_route(
        gql_schema=gql_schema,
        database=database,
        jwt_secret=jwt_secret,
        default_role=default_role,
        path=graphql_path,
        name="graphql",
    )

    graphiql_route = get_graphiql_route(graphiql_path="/graphiql", graphql_path=graphql_path, name="graphiql")

    _app = Starlette(
        routes=[graphql_route, graphiql_route],
        middleware=[Middleware(CORSMiddleware, allow_origins=["*"])],
        exception_handlers={HTTPException: http_exception},
        on_startup=[database.connect],
        on_shutdown=[database.disconnect],
    )

    return _app
