"""Tests for project_hail_mary.cli."""

from typer.testing import CliRunner

from project_hail_mary.cli import app

runner = CliRunner()


def test_hello():
    """The hello command echoes the project name."""
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "project-hAIl-mary" in result.stdout


def test_describe():
    """The describe command echoes the project's purpose."""
    result = runner.invoke(app, ["describe"])
    assert result.exit_code == 0
    assert "underrated" in result.stdout
