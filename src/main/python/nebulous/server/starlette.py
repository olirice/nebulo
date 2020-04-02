from __future__ import annotations

from typing import TYPE_CHECKING

import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse

from .starlette_graphql_view import GraphQLApp

# from flask_graphql import GraphQLView

if TYPE_CHECKING:
    from nebulous.gql.gql_database import GQLDatabase
    from nebulous.sql.sql_database import SQLDatabase
    from nebulous.user_config import UserConfig

__all__ = ["StarletteServer"]


class StarletteServer:
    def __init__(self, gql_db: GQLDatabase, sql_db: SQLDatabase, config: UserConfig):
        self.app = Starlette(debug=True)
        self.config = config
        self.gql_db = gql_db
        self.sql_db = sql_db
        self.setup()

    def setup(self):
        self.register_routes()
        self.register_session_handlers()

    def register_routes(self):
        @self.app.route("/")
        async def homepage(request):
            return JSONResponse({"hello": "world"})

        self.app.add_route(
            "/graphiql",
            GraphQLApp(schema=self.gql_db.schema, context={"session": self.sql_db.session}),
        )
        return

    def register_session_handlers(self):
        """Close database session when we're done"""

        @self.app.on_event("startup")
        async def startup():
            await self.sql_db.database.connect()

        @self.app.on_event("shutdown")
        async def shutdown():
            await self.sql_db.database.disconnect()

    def run(self):
        """Start serving requests from the application"""
        uvicorn.run(self.app, host="0.0.0.0", port=self.config.port)
