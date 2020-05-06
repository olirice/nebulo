from databases import Database
from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
from nebulo.server.exception import http_exception
from nebulo.server.routes import get_graphql_endpoint, graphiql_endpoint
from nebulo.sql.reflection.manager import reflect_sqla_models
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route


def create_app(database: Database) -> Starlette:
    """Create an ASGI App"""

    # Reflect database to sqla models
    connection_str = str(database.url)
    sqla_engine = create_engine(connection_str)
    sqla_models, sql_functions = reflect_sqla_models(engine=sqla_engine, schema="public")

    # Convert sqla models to graphql schema
    gql_schema = sqla_models_to_graphql_schema(sqla_models, sql_functions, resolve_async=True)

    # Build Starlette app
    graphql_endpoint = get_graphql_endpoint(gql_schema, database)
    routes = [Route("/", graphql_endpoint, methods=["POST"]), Route("/graphiql", graphiql_endpoint, methods=["GET"])]
    middleware = [Middleware(CORSMiddleware, allow_origins=["*"])]
    _app = Starlette(
        routes=routes,
        middleware=middleware,
        debug=True,
        exception_handlers={HTTPException: http_exception},
        on_startup=[database.connect],
        on_shutdown=[database.disconnect],
    )
    return _app
