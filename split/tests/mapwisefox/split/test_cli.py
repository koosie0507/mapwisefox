"""Tests for the Split command group and entrypoints."""

import runpy
from unittest.mock import Mock

from mapwisefox.split import run_command


def test_root_help_describes_available_commands(runner):
    result = runner.invoke(run_command, ["--help"])

    assert result.exit_code == 0
    assert "Divide Excel study workbooks among reviewers" in result.output
    assert "simple" in result.output
    assert "for-evaluation" in result.output


def test_command_help_describes_options(runner):
    result = runner.invoke(run_command, ["for-evaluation", "--help"])

    assert result.exit_code == 0
    assert "Number of reviewers" in result.output
    assert "Number of distinct reviewers" in result.output
    assert "Assistant Study QA criteria" in result.output


def test_simple_help_describes_options(runner):
    result = runner.invoke(run_command, ["simple", "--help"])

    assert result.exit_code == 0
    assert "Directory containing the Excel workbooks" in result.output
    assert "Filename pattern for input workbooks" in result.output
    assert "Number of non-overlapping reviewer bundles" in result.output


def test_module_entrypoint_invokes_command(monkeypatch):
    invocation = Mock()
    monkeypatch.setattr(type(run_command), "__call__", invocation)

    runpy.run_module("mapwisefox.split.__main__", run_name="__main__")

    invocation.assert_called_once()
