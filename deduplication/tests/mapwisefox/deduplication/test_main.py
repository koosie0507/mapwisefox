import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from mapwisefox.deduplication.__main__ import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_data_dir(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    return d


@patch("mapwisefox.deduplication.__main__._load_input_files")
@patch("mapwisefox.deduplication.__main__._run_dedupe")
@patch("mapwisefox.deduplication.__main__._merge_clusters")
def test_main_success_flow(mock_merge, mock_run, mock_load, runner, tmp_data_dir):
    mock_load.return_value = MagicMock()
    mock_run.return_value = MagicMock()
    mock_merge.return_value = MagicMock()

    input_dir = tmp_data_dir / "input"
    input_dir.mkdir()
    output_dir = tmp_data_dir / "output"

    result = runner.invoke(
        main,
        [
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0


@patch("mapwisefox.deduplication.__main__._load_input_files")
def test_main_invalid_input_dir(mock_load, runner, tmp_data_dir):
    mock_load.side_effect = Exception("Invalid dir")

    input_dir = tmp_data_dir / "invalid"
    input_dir.mkdir()

    result = runner.invoke(main, ["--input-dir", str(input_dir)])

    assert result.exit_code != 0


@patch("mapwisefox.deduplication.__main__._load_input_files")
@patch("mapwisefox.deduplication.__main__._run_dedupe")
@patch("mapwisefox.deduplication.__main__._merge_clusters")
def test_main_creates_output_dir(mock_merge, mock_run, mock_load, runner, tmp_data_dir):
    mock_load.return_value = MagicMock()
    mock_run.return_value = MagicMock()
    mock_merge.return_value = MagicMock()

    input_dir = tmp_data_dir / "input"
    input_dir.mkdir()
    output_dir = tmp_data_dir / "output_new"

    runner.invoke(
        main, ["--input-dir", str(input_dir), "--output-dir", str(output_dir)]
    )

    assert output_dir.exists()
