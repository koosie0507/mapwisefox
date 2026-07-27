from click.testing import CliRunner

from mapwisefox.metrics._cli import metrics


def test_mae_cli_prints_and_writes(tmp_path, trusted_files, evaluated_file, csv_file):
    output = tmp_path / "out.xlsx"
    result = CliRunner().invoke(
        metrics,
        [
            "-i",
            str(trusted_files[0]),
            "-i",
            str(trusted_files[1]),
            "-t",
            "score",
            "-o",
            str(output),
            "mae",
            str(evaluated_file),
        ],
    )
    assert result.exit_code == 0
    assert "Mean Absolute Error" in result.output
    assert "average score" in result.output
    assert output.exists()


def test_mae_cli_prints_without_output(trusted_files, evaluated_file):
    result = CliRunner().invoke(
        metrics,
        [
            "-i",
            str(trusted_files[0]),
            "-i",
            str(trusted_files[1]),
            "-t",
            "score",
            "mae",
            str(evaluated_file),
        ],
    )
    assert result.exit_code == 0
    assert "Mean Absolute Error" in result.output
