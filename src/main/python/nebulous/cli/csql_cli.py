import click

from nebulous.gql.gql_database import GQLDatabase
from nebulous.server.starlette import StarletteServer
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

    # Build flask webserver

    server = StarletteServer(gql_db, sql_db, config)
    import uvicorn

    uvicorn.run(server.app, host="0.0.0.0", port=server.config.port, loop="asyncio")
    # server.run()

    # uvicorn.run(app, host='0.0.0.0', port=8000)
    # server = FlaskServer(gql_db, sql_db, config)

    # Serve
    # server.run()
