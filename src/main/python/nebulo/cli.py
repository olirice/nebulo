from __future__ import annotations

import os

import click
import uvicorn
from graphql.utilities import print_schema
from nebulo.gql.sqla_to_gql import sqla_models_to_graphql_schema
from nebulo.sql.reflection_manager import reflect_sqla_models
from sqlalchemy import create_engine


@click.group()
@click.version_option(version="0.0.1")
def main(**kwargs):
    pass  # pragma: no cover


@main.command()
@click.option("-c", "--connection", default="sqlite:///")
@click.option("-p", "--port", default=5018)
@click.option("-h", "--host", default="0.0.0.0")
@click.option("-w", "--workers", default=1)
@click.option("-s", "--schema", default="public")
@click.option("--reload/--no-reload", default=True)
def run(connection, schema, host, port, reload, workers):
    """Run the GraphQL Server"""
    if reload and workers > 1:
        print("Reload not supported with workers > 1")
    else:
        # app = create_app(connection, schema, echo_queries)  # pragma: no cover
        os.environ["NEBULO_CONNECTION"] = connection
        os.environ["NEBULO_SCHEMA"] = schema

        uvicorn.run("nebulo.server.app:APP", host=host, workers=workers, port=port, log_level="info", reload=reload)


@main.command()
@click.option("-c", "--connection", default="sqlite:///")
@click.option("-s", "--schema", default="public")
@click.option("-o", "--out-file", type=click.File("w"), default=None)
def dump_schema(connection, schema, out_file):
    """Dump the GraphQL Schema to stdout or file"""
    engine = create_engine(connection)
    sqla_models = reflect_sqla_models(engine)
    schema = sqla_models_to_graphql_schema(sqla_models)
    schema_str = print_schema(schema)
    click.echo(schema_str, file=out_file)
