from __future__ import annotations

from typing import TYPE_CHECKING

import click
from graphql.utils.schema_printer import print_schema
from nebulo.server.flask import create_app

if TYPE_CHECKING:
    pass


@click.group()
@click.version_option(version="0.0.1")
def main(**kwargs):
    pass


@main.command()
@click.option("-c", "--connection", default="sqlite:///")
@click.option("-p", "--port", default=5018)
@click.option("-h", "--host", default="localhost")
@click.option("-s", "--schema", default=None)
@click.option("-e", "--echo-queries", is_flag=True, default=False)
def run(connection, schema, echo_queries, host, port):
    """Run the GraphQL Server"""
    app = create_app(connection, schema, echo_queries)
    app.run(host=host, port=port)


@main.command()
@click.option("-c", "--connection", default="sqlite:///")
@click.option("-s", "--schema", default=None)
@click.option("-o", "--out-file", type=click.File("w"), default=None)
def dump_schema(connection, schema, out_file):
    """Dump the GraphQL Schema to stdout or file"""
    app = create_app(connection, schema, echo_queries=False)
    schema = app.config["graphql_schema"]
    schema_str = print_schema(schema)
    click.echo(schema_str, file=out_file)
