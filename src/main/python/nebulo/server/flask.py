from __future__ import annotations

from typing import Optional

from flask import Flask
from flask_graphql import GraphQLView
from nebulo.gql.gql_database import GQLDatabase
from nebulo.sql.sql_database import SQLDatabase

__all__ = ["create_app"]


def create_app(connection: Optional[str], schema: str, echo_queries: bool, engine=None):
    app = Flask(__name__)
    app.config["connection"] = connection
    app.config["schema"] = schema
    app.config["echo_queries"] = echo_queries
    app.config["engine"] = engine

    app = register_database(app)
    app = register_graphql_schema(app)
    app = register_routes(app)
    return app


def register_database(app):
    sql_db = SQLDatabase(
        connection=app.config["connection"],
        schema=app.config["schema"],
        echo_queries=app.config["echo_queries"],
        engine=app.config["engine"],
    )
    app.config["database"] = sql_db

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        app.config["database"].session.remove()

    return app


def register_graphql_schema(app):
    sql_db = app.config["database"]
    gql_db = GQLDatabase(sql_db)
    app.config["graphql_schema"] = gql_db.schema
    return app


def register_routes(app):
    app.add_url_rule(
        "/graphql",
        view_func=GraphQLView.as_view(
            name="graphql",
            schema=app.config["graphql_schema"],
            graphiql=True,
            get_context=lambda: {"session": app.config["database"].session, "database": app.config["database"]},
        ),
    )
    return app
