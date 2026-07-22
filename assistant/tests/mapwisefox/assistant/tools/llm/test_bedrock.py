import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jinja2
import pytest

from mapwisefox.assistant.tools.llm import BedrockJSONGenerator, BedrockProvider


def _stream(*events):
    return [{"chunk": {"bytes": json.dumps(event).encode()}} for event in events]


def _openai_event(content):
    return {"choices": [{"delta": {"content": content}}]}


def _anthropic_event(delta):
    return {"type": "content_block_delta", "delta": delta}


def _generate(generator, response_format="json"):
    return generator.generate_json(
        jinja2.Template("system"),
        {},
        "user",
        response_format if isinstance(response_format, dict) else None,
    )


def test_bedrock_generates_json_from_anthropic_stream():
    client = MagicMock()
    client.invoke_model_with_response_stream.return_value = {
        "body": _stream(
            _anthropic_event({"type": "thinking_delta", "thinking": "think"}),
            _anthropic_event({"type": "text_delta", "text": '{"ok": true}'}),
        )
    }
    thinking, text = [], []
    generator = BedrockJSONGenerator(
        client,
        "anthropic.model",
        on_thinking=thinking.append,
        on_text=text.append,
    )

    assert _generate(generator, {"type": "object"}) == {"ok": True}
    assert thinking == ["think"]
    assert text
    request = json.loads(
        client.invoke_model_with_response_stream.call_args.kwargs["body"]
    )
    assert request["messages"] == [{"role": "user", "content": "user"}]
    assert "OUTPUT ONLY JSON" in request["system"]


def test_bedrock_generates_json_from_openai_stream_and_schema():
    client = MagicMock()
    client.invoke_model_with_response_stream.return_value = {
        "body": _stream(
            _openai_event("<reasoning>think</reasoning>"),
            _openai_event('{"ok": true}'),
        )
    }
    thinking, text = [], []
    generator = BedrockJSONGenerator(
        client,
        "openai.model",
        thinking=True,
        on_thinking=thinking.append,
        on_text=text.append,
    )

    assert _generate(generator, {"type": "object"}) == {"ok": True}
    assert thinking == ["think"]
    request = json.loads(
        client.invoke_model_with_response_stream.call_args.kwargs["body"]
    )
    assert request["response_format"]["type"] == "json_schema"
    assert request["reasoning_effort"] == "medium"


def test_bedrock_returns_empty_stream_as_non_json_error():
    client = MagicMock()
    client.invoke_model_with_response_stream.return_value = {"body": None}
    generator = BedrockJSONGenerator(client, "openai.model")

    with pytest.raises(ValueError, match="non-JSON"):
        _generate(generator)


def test_bedrock_rejects_unknown_model_through_public_generator_api():
    generator = BedrockJSONGenerator(MagicMock(), "unknown.model")

    with pytest.raises(ValueError, match="non-JSON"):
        _generate(generator)


def test_bedrock_handles_malformed_vendor_events_through_public_api():
    client = MagicMock()
    client.invoke_model_with_response_stream.return_value = {
        "body": [
            {},
            {"chunk": {}},
            {"chunk": {"bytes": json.dumps({"choices": []}).encode()}},
        ]
    }
    generator = BedrockJSONGenerator(client, "openai.model")

    with pytest.raises(ValueError, match="non-JSON"):
        _generate(generator)


def test_bedrock_public_generator_handles_empty_and_wrapped_openai_content():
    client = MagicMock()
    client.invoke_model_with_response_stream.return_value = {
        "body": _stream(
            _openai_event(""),
            _openai_event('prefix {"ok": true} suffix'),
        )
    }
    generator = BedrockJSONGenerator(client, "openai.model")

    assert _generate(generator) == {"ok": True}


def test_bedrock_public_generator_handles_malformed_anthropic_content():
    client = MagicMock()
    client.invoke_model_with_response_stream.return_value = {
        "body": _stream(
            {"type": "other"},
            {"type": "content_block_delta"},
            _anthropic_event({}),
            _anthropic_event({"type": "text_delta", "text": ""}),
        )
    }
    generator = BedrockJSONGenerator(client, "anthropic.model")

    with pytest.raises(ValueError, match="non-JSON"):
        _generate(generator)


def test_bedrock_provider_maps_models_and_checks_availability():
    client = MagicMock()
    runtime = MagicMock()
    client_module = SimpleNamespace(client=MagicMock(side_effect=[client, runtime]))
    exceptions = SimpleNamespace(
        ClientError=type("ClientError", (Exception,), {}),
        BotoCoreError=type("BotoCoreError", (Exception,), {}),
    )

    def importer(name):
        return client_module if name == "boto3" else exceptions

    with patch(
        "mapwisefox.assistant.tools.llm._bedrock.try_import", side_effect=importer
    ):
        errors = []
        provider = BedrockProvider(
            "gpt-oss:20b",
            "token",
            on_error=lambda message, error: errors.append(message),
        )
        client.get_foundation_model.return_value = {"model": "ok"}

        assert provider.ensure_model() is True
        assert isinstance(provider.new_json_generator(), BedrockJSONGenerator)
        client.get_foundation_model.side_effect = exceptions.BotoCoreError("offline")
        assert provider.ensure_model() is False

    assert errors
