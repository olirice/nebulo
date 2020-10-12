from click.testing import CliRunner
from nebulo.cli import dump_schema, main


def test_cli_version():
    runner = CliRunner()
    resp = runner.invoke(main, ["--version"])
    assert resp.exit_code == 0
    print(resp.output)
    assert "version" in resp.output


def test_cli_schema_dump(app_builder, connection_str):
    runner = CliRunner()

    _ = app_builder(
        """
    create table account (
        id serial primary key
    );
    """
    )

    resp = runner.invoke(dump_schema, ["-c", connection_str])
    assert resp.exit_code == 0
    print(resp.output)
    assert "Query" in resp.output
