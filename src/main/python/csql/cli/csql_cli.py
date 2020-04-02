import click
from flask import Flask
from flask_graphql import GraphQLView

from csql.user_config import UserConfig
from csql.sqla import SQLDatabase
from csql.gql import GQLDatabase


@click.group()
@click.version_option(version="0.1.0")
def main(**kwargs):
    pass


@main.command()
@click.option("-c", "--connection", default="sqlite:///")
@click.option("-p", "--port", default=5018)
@click.option("-s", "--schema", default="public")
@click.option("-q", "--graphql_route", default="/graphql")
@click.option("--graphiql/--no-graphiql", is_flag=True, default=True)
@click.option("-e", "--echo_queries", is_flag=True, default=False)
def run(**kwargs):
    # Set up configuration object
    config = UserConfig(**kwargs)
    click.echo(config)

    # Connect and refelct SQL database
    sql_db = SQLDatabase(config)

    # Reflect SQL to GQL
    gql_db = GQLDatabase(sql_db, config)

    # Configure Flask
    app = Flask(__name__)
    app.debug = True

    app.add_url_rule(
        config.graphql_route,
        view_func=GraphQLView.as_view(
            name="graphql",
            schema=gql_db.schema,
            graphiql=config.graphiql,
            get_context=lambda: {"session": sql_db.session},
        ),
    )

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        sql_db.session.remove()

    app.run(port=config.port)
