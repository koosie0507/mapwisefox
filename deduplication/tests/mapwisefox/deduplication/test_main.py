import re
from pathlib import Path

import pandas as pd
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


@pytest.fixture
def non_empty_df():
    return pd.DataFrame([{"title": "T1"}])


@patch("mapwisefox.deduplication.__main__._load_input_files")
@patch("mapwisefox.deduplication.__main__._run_dedupe")
@patch("mapwisefox.deduplication.__main__._merge_clusters")
def test_main_success_flow(
    mock_merge, mock_run, mock_load, runner, tmp_data_dir, non_empty_df
):
    mock_load.return_value = non_empty_df
    mock_run.return_value = non_empty_df
    mock_merge.return_value = MagicMock()

    input_dir = tmp_data_dir / "input"
    input_dir.mkdir()
    output_file = tmp_data_dir / "output" / "result.xlsx"

    result = runner.invoke(
        main,
        [
            "--input-dir",
            str(input_dir),
            "--output-file",
            str(output_file),
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
def test_main_creates_output_file_parent_dir(
    mock_merge, mock_run, mock_load, runner, tmp_data_dir, non_empty_df
):
    mock_load.return_value = non_empty_df
    mock_run.return_value = non_empty_df
    mock_merge.return_value = MagicMock()

    input_dir = tmp_data_dir / "input"
    input_dir.mkdir()
    output_file = tmp_data_dir / "output_new" / "result.xlsx"

    runner.invoke(
        main, ["--input-dir", str(input_dir), "--output-file", str(output_file)]
    )

    assert output_file.parent.exists()


@patch("mapwisefox.deduplication.__main__._load_input_files")
@patch("mapwisefox.deduplication.__main__._run_dedupe")
@patch("mapwisefox.deduplication.__main__._merge_clusters")
def test_main_writes_to_explicit_output_file(
    mock_merge, mock_run, mock_load, runner, tmp_data_dir, non_empty_df
):
    mock_load.return_value = non_empty_df
    mock_run.return_value = non_empty_df
    mock_merge.return_value = MagicMock()

    input_dir = tmp_data_dir / "input"
    input_dir.mkdir()
    output_file = tmp_data_dir / "custom" / "result.xlsx"

    runner.invoke(
        main, ["--input-dir", str(input_dir), "--output-file", str(output_file)]
    )

    to_excel_args = mock_merge.return_value.to_excel.call_args.args
    assert Path(to_excel_args[0]) == output_file


@patch("mapwisefox.deduplication.__main__._load_input_files")
@patch("mapwisefox.deduplication.__main__._run_dedupe")
@patch("mapwisefox.deduplication.__main__._merge_clusters")
def test_main_default_output_file_lands_under_data_output(
    mock_merge, mock_run, mock_load, runner, non_empty_df
):
    mock_load.return_value = non_empty_df
    mock_run.return_value = non_empty_df
    mock_merge.return_value = MagicMock()

    with runner.isolated_filesystem():
        input_dir = Path("input")
        input_dir.mkdir()

        result = runner.invoke(main, ["--input-dir", str(input_dir)])

        assert result.exit_code == 0
        to_excel_args = mock_merge.return_value.to_excel.call_args.args
        output_file = Path(to_excel_args[0])
        assert output_file.parent == Path.cwd() / "data" / "output"
        assert re.match(r"^\d{8}-\d{6}-deduplicated-records\.xlsx$", output_file.name)


def test_main_default_input_dir_has_no_weekly_bucket():
    default = main.params[0].default

    assert Path(default) == Path.cwd() / "data" / "input"


def test_main_errors_when_input_dir_missing(runner, tmp_data_dir):
    missing_dir = tmp_data_dir / "does-not-exist"

    result = runner.invoke(main, ["--input-dir", str(missing_dir)])

    assert result.exit_code != 0
    assert "does not exist" in result.output
    assert str(missing_dir) in result.output


def test_main_errors_when_input_dir_has_no_recognized_files(runner, tmp_data_dir):
    input_dir = tmp_data_dir / "input"
    input_dir.mkdir()
    (input_dir / "notes.txt").write_text("not a csv or bib file")

    result = runner.invoke(main, ["--input-dir", str(input_dir)])

    assert result.exit_code != 0
    assert "No .csv or .bib files found" in result.output
    assert str(input_dir) in result.output


@patch("mapwisefox.deduplication.__main__._load_input_files")
@patch("mapwisefox.deduplication.__main__._run_dedupe")
@patch("mapwisefox.deduplication.__main__._merge_clusters")
def test_main_derives_training_and_settings_paths_from_config_dir(
    mock_merge, mock_run, mock_load, runner, tmp_data_dir, non_empty_df
):
    mock_load.return_value = non_empty_df
    mock_run.return_value = non_empty_df
    mock_merge.return_value = MagicMock()

    input_dir = tmp_data_dir / "input"
    input_dir.mkdir()
    config_dir = tmp_data_dir / "dedupe-config"

    runner.invoke(
        main,
        [
            "--input-dir",
            str(input_dir),
            "--dd-config-dir",
            str(config_dir),
        ],
    )

    args = mock_run.call_args.args
    assert Path(args[1]) == config_dir / "training.json"
    assert Path(args[2]) == config_dir / "settings.dedupe"


@patch("mapwisefox.deduplication.__main__._load_input_files")
@patch("mapwisefox.deduplication.__main__._run_dedupe")
@patch("mapwisefox.deduplication.__main__._merge_clusters")
def test_main_passes_threshold_to_run_dedupe(
    mock_merge, mock_run, mock_load, runner, tmp_data_dir, non_empty_df
):
    mock_load.return_value = non_empty_df
    mock_run.return_value = non_empty_df
    mock_merge.return_value = MagicMock()

    input_dir = tmp_data_dir / "input"
    input_dir.mkdir()

    result = runner.invoke(
        main,
        ["--input-dir", str(input_dir), "--threshold", "0.7"],
    )

    assert result.exit_code == 0
    assert mock_run.call_args.kwargs["threshold"] == 0.7
