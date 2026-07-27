from click.testing import CliRunner

from mapwisefox.metrics._cli import metrics


def test_metrics_help_displays_group_description():
    result = CliRunner().invoke(metrics, ["--help"])
    assert result.exit_code == 0
    assert "agreement metrics among raters" in result.output


def test_metrics_rejects_unsupported_input_type(tmp_path, csv_file):
    bib = tmp_path / "data.bib"
    bib.write_text("@article{x, title={x}}\n")
    result = CliRunner().invoke(
        metrics, ["-i", str(bib), "mae", str(csv_file([{"id": 1, "x": 1}]))]
    )
    assert result.exit_code != 0
    assert "does not support '.bib'" in result.output


def test_metrics_load_error_reports_file_name(csv_file):
    broken = csv_file([{"id": 1, "score": "not-a-number"}], file_name="broken.csv")
    # Write an invalid Excel-looking CSV so pandas raises while loading
    broken.write_text("garbage\x00\x01\x02")
    result = CliRunner().invoke(
        metrics, ["-i", str(broken), "mae", str(csv_file([{"id": 1, "score": 1}]))]
    )
    assert result.exit_code != 0
    assert "could not load file 'broken.csv'" in result.output


def test_metrics_main_entrypoint_imports_cli():
    import mapwisefox.metrics.__main__ as main_module

    assert main_module.cli is metrics
