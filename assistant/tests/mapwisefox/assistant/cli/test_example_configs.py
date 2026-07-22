import json

from mapwisefox.assistant._base import assistant


def test_study_selection_example_config_is_valid(runner, example_selection_config_path):
    result = runner.invoke(
        assistant,
        [
            "validate-config",
            "--kind",
            "study-selection",
            "--config-file",
            str(example_selection_config_path),
        ],
    )

    assert result.exit_code == 0, result.output


def test_study_qa_example_config_is_valid(runner, example_qa_config_path):
    result = runner.invoke(
        assistant,
        [
            "validate-config",
            "--kind",
            "study-qa",
            "--config-file",
            str(example_qa_config_path),
        ],
    )

    assert result.exit_code == 0, result.output


def test_example_configs_are_short_enough_for_a_usage_example(
    example_selection_config_path, example_qa_config_path
):
    selection = json.loads(example_selection_config_path.read_text())
    qa = json.loads(example_qa_config_path.read_text())

    assert len(selection["inclusion_criteria"]) <= 3
    assert len(selection["exclusion_criteria"]) <= 3
    assert 3 <= len(qa["criteria"]) <= 4
