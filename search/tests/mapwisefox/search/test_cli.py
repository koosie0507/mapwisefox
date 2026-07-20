from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner
from mapwisefox.search.__main__ import main


def test_main_no_config():
    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code != 0
    assert "Error: Missing option '--config'" in result.output


def test_main_invalid_config_path(tmp_path):
    runner = CliRunner()
    non_existent_config = tmp_path / "non_existent.yaml"

    result = runner.invoke(main, ["--config", str(non_existent_config)])
    assert result.exit_code != 0
    assert "does not exist" in result.output


@pytest.mark.parametrize(
    "backend",
    [
        "ConsoleBackend",
        "ScienceDirectBackend",
        "ScopusBackend",
        "SpringerBackend",
        "WebOfScienceBackend",
    ],
)
@pytest.mark.parametrize(
    "adapter",
    [
        "AcmDSLAdapter",
        "ScienceDirectDSLAdapter",
        "ScopusDSLAdapter",
        "SpringerDSLAdapter",
        "WebOfScienceDSLAdapter",
        "XploreDSLAdapter",
    ],
)
def test_main_success(tmp_path, adapter, backend):
    runner = CliRunner()

    from mapwisefox.search._config import SearchConfig, BackendSpec, BackendRef

    mock_config = SearchConfig(
        query="test query",
        backends=[
            BackendSpec(
                name="test-backend", adapter=adapter, backend=BackendRef(type=backend)
            )
        ],
    )

    with (
        patch("mapwisefox.search.__main__._load_config", return_value=mock_config),
        patch("mapwisefox.search.__main__._execute") as mock_execute,
        patch("mapwisefox.search.__main__.Parser") as mock_parser_cls,
    ):

        # Mock the parser to return a dummy IR
        mock_parser = mock_parser_cls.return_value
        mock_parser.return_value = MagicMock()  # Dummy QueryIR

        config_path = tmp_path / "config.yaml"
        config_path.write_text("dummy")

        result = runner.invoke(main, ["--config", str(config_path)])

        assert result.exit_code == 0
        assert mock_execute.called


@pytest.mark.parametrize(
    "backend",
    [
        "ConsoleBackend",
        "ScienceDirectBackend",
        "ScopusBackend",
        "SpringerBackend",
        "WebOfScienceBackend",
    ],
)
@pytest.mark.parametrize(
    "adapter",
    [
        "AcmDSLAdapter",
        "ScienceDirectDSLAdapter",
        "ScopusDSLAdapter",
        "SpringerDSLAdapter",
        "WebOfScienceDSLAdapter",
        "XploreDSLAdapter",
    ],
)
def test_main_data_dir_override(tmp_path, adapter, backend):
    runner = CliRunner()

    from mapwisefox.search._config import SearchConfig, BackendSpec, BackendRef

    mock_config = SearchConfig(
        query="test query",
        backends=[
            BackendSpec(
                name="test-backend", adapter=adapter, backend=BackendRef(type=backend)
            )
        ],
    )

    custom_data_dir = tmp_path / "custom-data"
    custom_data_dir.mkdir()

    with (
        patch("mapwisefox.search.__main__._load_config", return_value=mock_config),
        patch("mapwisefox.search.__main__._execute"),
        patch("mapwisefox.search.__main__.Parser") as mock_parser_cls,
        patch("mapwisefox.search.__main__._ensure_results_dir") as mock_ensure_dir,
    ):

        mock_parser = mock_parser_cls.return_value
        mock_parser.return_value = MagicMock()

        config_path = tmp_path / "config.yaml"
        config_path.write_text("dummy")

        result = runner.invoke(
            main, ["--config", str(config_path), "--data-dir", str(custom_data_dir)]
        )

        assert result.exit_code == 0
        args, _ = mock_ensure_dir.call_args
        assert args[0] == str(custom_data_dir)
