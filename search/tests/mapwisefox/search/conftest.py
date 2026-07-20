"""Shared fixtures for CLI-level integration tests."""

import io
from contextlib import redirect_stdout
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from mapwisefox.search.__main__ import main
from mapwisefox.search.backends import ConsoleBackend
from mapwisefox.search.dsl.adapters import (
    AcmDSLAdapter,
    ScienceDirectDSLAdapter,
    ScopusDSLAdapter,
    SpringerDSLAdapter,
    WebOfScienceDSLAdapter,
    XploreDSLAdapter,
)


@pytest.fixture(scope="session")
def docs_basic_config_path():
    """Path to the documented safe-usage example config (all adapters, ConsoleBackend)."""
    path = Path(__file__).parents[3] / "config.basic.yaml"
    assert path.exists(), f"config.basic.yaml not found at {path}"
    return path


@pytest.fixture
def ersa_query_objects_by_adapter(parse, ersa_query_text):
    """Dict of adapter name -> QueryObject for the ERSA example query.

    Computes the expected query/filters/regex by running each real adapter
    directly against the shared ``ersa_query_text`` fixture.
    """
    ir = parse(ersa_query_text)
    adapters = {
        "AcmDSLAdapter": AcmDSLAdapter(),
        "ScienceDirectDSLAdapter": ScienceDirectDSLAdapter(),
        "ScopusDSLAdapter": ScopusDSLAdapter(),
        "SpringerDSLAdapter": SpringerDSLAdapter(),
        "WebOfScienceDSLAdapter": WebOfScienceDSLAdapter(),
        "XploreDSLAdapter": XploreDSLAdapter(),
    }
    return {name: adapter.adapt(ir) for name, adapter in adapters.items()}


@pytest.fixture
def render_console_block():
    """Factory to capture ConsoleBackend's exact printed output for a QueryObject."""

    def _render(query_obj):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ConsoleBackend()(query_obj)
        return buf.getvalue()

    return _render


@pytest.fixture
def basic_usage_result(docs_basic_config_path, tmp_path):
    """Runs the real search CLI with config.basic.yaml, captures the result."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["--config", str(docs_basic_config_path), "--data-dir", str(tmp_path)]
    )
    return result


@pytest.fixture
def single_backend_config_path(tmp_path):
    """Factory to write a minimal single-backend YAML config for real-backend tests.

    Usage:
        config_path = single_backend_config_path(
            query="...",
            backend_name="ScienceDirect",
            adapter="ScienceDirectDSLAdapter",
            backend_type="ScienceDirectBackend",
            backend_options={"api_key": "fake", "csv_path": "sd.csv"}
        )
    """

    def _writer(query, backend_name, adapter, backend_type, backend_options=None):
        config = {
            "query": query,
            "backends": [
                {
                    "name": backend_name,
                    "adapter": adapter,
                    "backend": {
                        "type": backend_type,
                        "options": backend_options or {},
                    },
                }
            ],
        }
        config_path = tmp_path / f"{backend_name.lower().replace(' ', '_')}_config.yaml"
        config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
        return config_path

    return _writer
