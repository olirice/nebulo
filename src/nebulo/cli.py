from __future__ import annotations

import click
import uvicorn
from graphql.utilities import print_schema
from nebulo import VERSION
from nebulo.env import EnvManager
from sqlalchemy import create_engine


@click.group()
@click.version_option(version=VERSION)
def main(**kwargs):
    pass  # pragma: no cover


@main.command()
@click.option("-c", "--connection", help="Database connection string")
@click.option("-p", "--port", default=5034, help="Web server port")
@click.option("-h", "--host", default="0.0.0.0", help="Host address")
@click.option("-w", "--workers", default=1, help="Number of parallel workers")
@click.option("-s", "--schema", default="public", help="SQL schema name")
@click.option("--jwt-identifier", default=None, help='JWT composite type identifier e.g. "public.jwt"')
@click.option("--jwt-secret", default=None, help="Secret key for JWT encryption")
@click.option("--reload/--no-reload", default=False, help="Reload if source files change")
@click.option("--default-role", type=str, default=None, help="Default PostgreSQL role for anonymous users")
def run(connection, schema, host, port, jwt_identifier, jwt_secret, reload, workers, default_role):
    """Run the GraphQL Web Server"""
    if reload and workers > 1:
        print("Reload not supported with workers > 1")
    else:

        with EnvManager(
            NEBULO_CONNECTION=connection,
            NEBULO_SCHEMA=schema,
            NEBULO_JWT_IDENTIFIER=jwt_identifier,
            NEBULO_JWT_SECRET=jwt_secret,
            NEBULO_DEFAULT_ROLE=default_role,
        ):

            uvicorn.run("nebulo.server.app:APP", host=host, workers=workers, port=port, log_level="info", reload=reload)


@main.command()
@click.option("-c", "--connection", help="Database connection string")
@click.option("-s", "--schema", default="public", help="SQL schema name")
@click.option("-o", "--out-file", type=click.File("w"), default=None, help="Output file path")
def dump_schema(connection, schema, out_file):
    """Dump the GraphQL Schema to stdout or file"""
    from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
    from nebulo.sql.reflection.manager import reflect_sqla_models

    engine = create_engine(connection)
    sqla_models, sql_functions = reflect_sqla_models(engine, schema=schema)
    schema = sqla_models_to_graphql_schema(sqla_models, sql_functions)
    schema_str = print_schema(schema)
    click.echo(schema_str, file=out_file)
