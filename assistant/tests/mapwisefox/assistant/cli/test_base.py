import pytest

from mapwisefox.assistant._base import assistant


@pytest.mark.parametrize(
    "provider", ["ollama", "openai", "anthropic", "google", "bedrock"]
)
def test_assistant_accepts_each_provider_for_validation_command(
    runner, valid_selection_config_path, provider
):
    args = ["--provider", provider]
    if provider in {"openai", "anthropic", "google", "bedrock"}:
        args += ["--api-key", "test-key"]
    args += [
        "validate-config",
        "--kind",
        "study-selection",
        "--config-file",
        str(valid_selection_config_path),
    ]

    result = runner.invoke(assistant, args)

    assert result.exit_code == 0, result.output


def test_assistant_requires_api_key_for_openai(
    runner, valid_selection_config_path, monkeypatch
):
    monkeypatch.delenv("MWF_ASSISTANT_API_KEY", raising=False)
    result = runner.invoke(
        assistant,
        [
            "--provider",
            "openai",
            "validate-config",
            "--kind",
            "study-selection",
            "--config-file",
            str(valid_selection_config_path),
        ],
    )

    assert result.exit_code != 0
    assert "API key" in result.output


def test_assistant_clamps_ollama_port(runner, valid_selection_config_path):
    result = runner.invoke(
        assistant,
        [
            "--ollama-port",
            "1",
            "validate-config",
            "--kind",
            "study-selection",
            "--config-file",
            str(valid_selection_config_path),
        ],
    )

    assert result.exit_code == 0
