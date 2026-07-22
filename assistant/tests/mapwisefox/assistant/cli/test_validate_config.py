from mapwisefox.assistant._base import assistant


def test_validate_config_is_registered_on_assistant_group(runner):
    result = runner.invoke(assistant, ["--help"])

    assert "validate-config" in result.output


def test_assistant_group_dispatches_to_validate_config(
    runner, valid_selection_config_path
):
    result = runner.invoke(
        assistant,
        [
            "validate-config",
            "--kind",
            "study-selection",
            "--config-file",
            str(valid_selection_config_path),
        ],
    )

    assert result.exit_code == 0
