from __future__ import annotations
from typing import TYPE_CHECKING
from flask import Flask
from flask_graphql import GraphQLView

if TYPE_CHECKING:
    from csql.gql import GQLDatabase
    from csql.sqla import SQLDatabase
    from csql.user_config import UserConfig

__all__ = ["FlaskServer"]


class FlaskServer:
    def __init__(self, gql_db: GQLDatabase, sql_db: SQLDatabase, config: UserConfig):
        self.app = Flask(__name__)
        self.app.debug = True
        self.config = config
        self.gql_db = gql_db
        self.sql_db = sql_db
        self.setup()

    def setup(self):
        self.register_routes()
        self.register_session_teardown()

    def register_routes(self):
        self.app.add_url_rule(
            self.config.graphql_route,
            view_func=GraphQLView.as_view(
                name="graphql",
                schema=self.gql_db.schema,
                graphiql=self.config.graphiql,
                get_context=lambda: {"session": self.sql_db.session},
            ),
        )

    def register_session_teardown(self):
        """Close database session when we're done"""

        @self.app.teardown_appcontext
        def shutdown_session(exception=None):
            self.sql_db.session.remove()

    def run(self):
        """Start serving requests from the application"""
        self.app.run(port=self.config.port)
