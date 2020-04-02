import click

from nebulous.server.flask import create_app


@click.group()
@click.version_option(version="0.1.0")
def main(**kwargs):
    pass


@main.command()
@click.option("-c", "--connection", default="sqlite:///")
@click.option("-p", "--port", default=5018)
@click.option("-h", "--host", default="localhost")
@click.option("-s", "--schema", default=None)
@click.option("-e", "--echo-queries", is_flag=True, default=False)
@click.option("--demo/--no-demo", is_flag=True, default=False)
def run(connection, schema, echo_queries, demo, host, port):
    app = create_app(connection, schema, echo_queries, demo)
    app.run(host=host, port=port)
