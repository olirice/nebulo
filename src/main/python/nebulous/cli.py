import click

from nebulous.gql.gql_database import GQLDatabase
from nebulous.server.flask import FlaskServer
from nebulous.sql.sql_database import SQLDatabase
from nebulous.user_config import UserConfig


@click.group()
@click.version_option(version="0.1.0")
def main(**kwargs):
    pass


@main.command()
@click.option("-c", "--connection", default="sqlite:///")
@click.option("-p", "--port", default=5018)
@click.option("-s", "--schema", default=None)
@click.option("-q", "--graphql-route", default="/graphql")
@click.option("-e", "--echo-queries", is_flag=True, default=False)
@click.option("--graphiql/--no-graphiql", is_flag=True, default=True)
@click.option("--demo/--no-demo", is_flag=True, default=False)
def run(**kwargs):
    # Set up configuration object
    config = UserConfig(**kwargs)

    # Connect and refelct SQL database
    sql_db = SQLDatabase(config)

    # Reflect SQL to GQL
    gql_db = GQLDatabase(sql_db, config)

    app = FlaskServer(gql_db, sql_db, config)
    app.run()


if __name__ == "__main__":
    # Set up configuration object
    config = UserConfig(
        connection="postgresql://postgres:password@localhost:5432/postgres",
        schema="public",
        demo=True,
        port=5052,
        graphql_route="/graphql",
        graphiql=True,
        echo_queries=False,
    )

    sql_db = SQLDatabase(config)
    gql_db = GQLDatabase(sql_db, config)
    app = FlaskServer(gql_db, sql_db, config)
    app.run()
