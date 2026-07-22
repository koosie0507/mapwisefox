from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jinja2
import pytest

from mapwisefox.assistant.tools.llm._openai import OpenAIJSONGenerator, OpenAIProvider


class SchemaParam(dict):
    pass


def _module(client=None):
    return SimpleNamespace(
        ResponseFormatTextJSONSchemaConfigParam=SchemaParam,
        OpenAI=MagicMock(return_value=client),
        APIError=type("APIError", (Exception,), {}),
    )


def _stream(events):
    stream = MagicMock()
    stream.__enter__.return_value = events
    stream.__exit__.return_value = False
    return stream


def test_openai_generator_streams_text_and_builds_json_object_format():
    client = MagicMock()
    events = [
        SimpleNamespace(type="response.created"),
        SimpleNamespace(type="response.output_text.delta", delta='{"ok": true}'),
        SimpleNamespace(type="response.completed"),
    ]
    client.responses.stream.return_value = _stream(events)
    generator = OpenAIJSONGenerator(client, "model")

    result = generator.generate_json(jinja2.Template("system"), {}, "user")

    assert result == {"ok": True}
    assert client.responses.stream.call_args.kwargs["text_format"] == {
        "type": "json_object"
    }


def test_openai_generator_builds_schema_format_and_reports_error_event():
    client = MagicMock()
    client.responses.stream.return_value = _stream(
        [SimpleNamespace(type="error"), SimpleNamespace(type="ignored")]
    )
    errors = []
    generator = OpenAIJSONGenerator(
        client, "model", on_error=lambda message, error: errors.append(message)
    )

    with pytest.raises(ValueError, match="non-JSON"):
        generator.generate_json(
            jinja2.Template("system"), {}, "user", {"type": "object"}
        )

    format_arg = client.responses.stream.call_args.kwargs["text_format"]
    assert format_arg["type"] == "json_schema"
    assert errors[0] == ""


def test_openai_generator_returns_empty_text_on_stream_type_error():
    client = MagicMock()
    client.responses.stream.side_effect = TypeError("unsupported")
    generator = OpenAIJSONGenerator(client, "model")

    with pytest.raises(ValueError, match="non-JSON"):
        generator.generate_json(jinja2.Template("system"), {}, "user")


def test_openai_provider_ensures_model_and_handles_api_error():
    api_error = type("APIError", (Exception,), {})
    client = MagicMock()
    client.models.retrieve.return_value = object()
    module = SimpleNamespace(
        ResponseFormatTextJSONSchemaConfigParam=SchemaParam,
        OpenAI=MagicMock(return_value=client),
        APIError=api_error,
    )

    with patch(
        "mapwisefox.assistant.tools.llm._openai.try_import", return_value=module
    ):
        provider = OpenAIProvider("model", "key", on_error=lambda *args: None)
        assert provider.ensure_model() is True
        client.models.retrieve.side_effect = api_error("offline")
        assert provider.ensure_model() is False
