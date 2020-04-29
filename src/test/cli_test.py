from click.testing import CliRunner
from nebulo.cli import dump_schema, main


def test_cli_version():
    runner = CliRunner()
    resp = runner.invoke(main, ["--version"])
    assert resp.exit_code == 0
    print(resp.output)
    assert "version" in resp.output


def test_cli_schema_dump(connection_str):
    runner = CliRunner()
    resp = runner.invoke(dump_schema, ["-c", connection_str])
    assert resp.exit_code == 0
    print(resp.output)
    assert "Query" in resp.output
