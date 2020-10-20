# Public API

Nebulo exposes a minimal public API to allow the internals to change freely. The public API is defined as anything documented on this page.

For a complete example see [the SQLAlchemy interop example](sqlalchemy_interop.md)

``` python
from databases import Database
from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
from nebulo.server.exception import http_exception
from nebulo.server.routes import GRAPHIQL_STATIC_FILES, get_graphql_route, graphiql_route
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.routing import Mount, Route

from myapp.sqla_models import Author, Book
from myapp.config import DATABASE_URI


def create_app(connection_str, sqla_models) -> Starlette:
    """Create the Starlette app"""

    database = Database(connection)

    # Convert sqla models to graphql schema
    gql_schema = sqla_models_to_graphql_schema(sqla_models=sqla_models)

    graphql_path = '/'

    # Build the Starlette GraphQL Route
    graphql_route = get_graphql_route(
        gql_schema=gql_schema,
        database=database,
        jwt_secret=jwt_secret,
        default_role=default_role,
        path=graphql_path,
        name='graphql'
    )

    # Build the Starlette GraphiQL Route and StaticFiles
    graphiql_route = get_graphiql_route(
        graphiql_path='/graphiql',
        graphql_path=graphql_path,
        name='graphiql'
    )

    # Instantiate the Starlette app
    _app = Starlette(
        routes=[graphql_route, graphiql_route],
        exception_handlers={HTTPException: http_exception},
        on_startup=[database.connect],
        on_shutdown=[database.disconnect],
    )

    return _app



# Instantiate the app
APP = create_app(connection_str=DATABASE_URI, sqla_models=[Author, Book])
```

### Reflection

Utilities for reflecting SQL entities as GraphQL entities.

##### SQLA to GraphQL
----

::: nebulo.gql.sqla_to_gql.sqla_models_to_graphql_schema
    :docstring:


### Server

Helpers to serve the GraphQL schema.

##### Routes
----

::: nebulo.server.routes.get_graphql_route
    :docstring:

----

::: nebulo.server.routes.get_graphiql_route
    :docstring:

##### Exception Handling
----

::: nebulo.server.exception.http_exception
    :docstring:



