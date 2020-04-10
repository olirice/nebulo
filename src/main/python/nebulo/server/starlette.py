from databases import Database
from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
from nebulo.server.exception import http_exception
from nebulo.server.routes import get_graphql_endpoint, graphiql_endpoint
from nebulo.sql.sql_database import SQLDatabase
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route


def create_app(database: Database) -> Starlette:
    """Create an ASGI App"""

    connection_str = str(database.url)

    reflection_manager = SQLDatabase(connection=connection_str, schema="public")

    gql_schema = sqla_models_to_graphql_schema(reflection_manager.models, resolve_async=True)

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
