import json

import pytest

from mapwisefox.assistant.config._validate import validate_config


@pytest.fixture
def invalid_selection_config_path(tmp_path):
    path = tmp_path / "selection.json"
    path.write_text(json.dumps({"review_topic": "find good papers"}))
    return path


def test_validate_config_exits_zero_for_valid_selection_config(
    runner, valid_selection_config_path
):
    result = runner.invoke(
        validate_config,
        [
            "--kind",
            "study-selection",
            "--config-file",
            str(valid_selection_config_path),
        ],
    )

    assert result.exit_code == 0


def test_validate_config_prints_success_message(runner, valid_selection_config_path):
    result = runner.invoke(
        validate_config,
        [
            "--kind",
            "study-selection",
            "--config-file",
            str(valid_selection_config_path),
        ],
    )

    assert "valid" in result.output.lower()


def test_validate_config_exits_nonzero_for_invalid_config(
    runner, invalid_selection_config_path
):
    result = runner.invoke(
        validate_config,
        [
            "--kind",
            "study-selection",
            "--config-file",
            str(invalid_selection_config_path),
        ],
    )

    assert result.exit_code != 0


def test_validate_config_reports_errors_for_invalid_config(
    runner, invalid_selection_config_path
):
    result = runner.invoke(
        validate_config,
        [
            "--kind",
            "study-selection",
            "--config-file",
            str(invalid_selection_config_path),
        ],
    )

    assert "inclusion_criteria" in result.output


def test_validate_config_supports_qa_kind(runner, tmp_path):
    path = tmp_path / "qa.json"
    path.write_text(
        json.dumps(
            {
                "topic": "entity resolution",
                "criteria": [
                    {
                        "label": "re1",
                        "category": "reporting",
                        "question": "Is it formal?",
                        "description": "assess tone",
                        "scoring": "1 to 10",
                    }
                ],
            }
        )
    )

    result = runner.invoke(
        validate_config, ["--kind", "study-qa", "--config-file", str(path)]
    )

    assert result.exit_code == 0
