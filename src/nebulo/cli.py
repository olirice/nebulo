from __future__ import annotations

import click
import uvicorn
from graphql.utilities import print_schema
from nebulo.env import EnvManager
from sqlalchemy import create_engine


@click.group()
@click.version_option(version="0.0.1")
def main(**kwargs):
    pass  # pragma: no cover


@main.command()
@click.option("-c", "--connection", default="sqlite:///")
@click.option("-p", "--port", default=5034)
@click.option("-h", "--host", default="0.0.0.0")
@click.option("-w", "--workers", default=1)
@click.option("-s", "--schema", default="public")
@click.option("--jwt-identifier", default=None)
@click.option("--jwt-secret", default=None)
@click.option("--reload/--no-reload", default=False)
def run(connection, schema, host, port, jwt_identifier, jwt_secret, reload, workers):
    """Run the GraphQL Server"""
    if reload and workers > 1:
        print("Reload not supported with workers > 1")
    else:

        with EnvManager(
            NEBULO_CONNECTION=connection,
            NEBULO_SCHEMA=schema,
            NEBULO_JWT_IDENTIFIER=jwt_identifier,
            NEBULO_JWT_SECRET=jwt_secret,
        ):

            uvicorn.run("nebulo.server.app:APP", host=host, workers=workers, port=port, log_level="info", reload=reload)


@main.command()
@click.option("-c", "--connection", default="sqlite:///")
@click.option("-s", "--schema", default="public")
@click.option("-o", "--out-file", type=click.File("w"), default=None)
def dump_schema(connection, schema, out_file):
    """Dump the GraphQL Schema to stdout or file"""
    from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
    from nebulo.sql.reflection.manager import reflect_sqla_models

    engine = create_engine(connection)
    sqla_models, sql_functions = reflect_sqla_models(engine, schema=schema)
    schema = sqla_models_to_graphql_schema(sqla_models, sql_functions)
    schema_str = print_schema(schema)
    click.echo(schema_str, file=out_file)
