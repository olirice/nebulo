import click
from csql.user_config import UserConfig
from csql.sql.sql_database import SQLDatabase
from csql.gql.gql_database import GQLDatabase
from csql.server.flask import FlaskServer


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

    # Connect and refelct SQL database
    sql_db = SQLDatabase(config)

    # Reflect SQL to GQL
    gql_db = GQLDatabase(sql_db, config)

    # Build flask webserver
    server = FlaskServer(gql_db, sql_db, config)

    # Serve
    server.run()
