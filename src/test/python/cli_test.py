from click.testing import CliRunner

from nebulous.cli import main


def test_cli_version():
    runner = CliRunner()
    resp = runner.invoke(main, ["--version"])
    assert resp.exit_code == 0
    print(resp.output)
    assert "version" in resp.output
