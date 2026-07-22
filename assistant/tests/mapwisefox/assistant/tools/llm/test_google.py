from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jinja2
import pytest

from mapwisefox.assistant.tools.llm._google import GoogleJSONGenerator, GoogleProvider


def _part(text, thought=False):
    return SimpleNamespace(text=text, thought=thought)


def _chunk(parts):
    return SimpleNamespace(
        candidates=[SimpleNamespace(content=SimpleNamespace(parts=parts))]
    )


def test_google_generator_streams_thoughts_and_text():
    client = MagicMock()
    client.models.generate_content_stream.return_value = iter(
        [_chunk([_part("think", True), _part('{"ok": true}')]), _chunk(None)]
    )
    thoughts, text = [], []
    generator = GoogleJSONGenerator(
        client,
        "gemini-pro",
        thinking_level="low",
        on_thinking=thoughts.append,
        on_text=text.append,
    )

    result = generator.generate_json(
        jinja2.Template("system"), {}, "user", {"type": "object"}
    )

    assert result == {"ok": True}
    assert thoughts == ["think"]
    assert client.models.generate_content_stream.call_args.kwargs["config"][
        "response_json_schema"
    ] == {"type": "object"}


def test_google_generator_returns_empty_text_and_reports_errors():
    client = MagicMock()
    client.models.generate_content_stream.side_effect = RuntimeError("offline")
    errors = []
    generator = GoogleJSONGenerator(
        client, "gemini-pro", on_error=lambda msg, err: errors.append(msg)
    )

    with pytest.raises(ValueError, match="non-JSON"):
        generator.generate_json(jinja2.Template("system"), {}, "user")
    assert errors[0] == "something went horribly wrong"


def test_google_provider_ensures_model_and_handles_api_error():
    api_error = type("APIError", (Exception,), {})
    client = MagicMock()
    module = SimpleNamespace(Client=MagicMock(return_value=client), APIError=api_error)
    errors = []
    with patch(
        "mapwisefox.assistant.tools.llm._google.try_import", return_value=module
    ):
        provider = GoogleProvider(
            "model", "key", on_error=lambda msg, err: errors.append(msg)
        )
        client.models.get.return_value = object()
        assert provider.ensure_model() is True
        client.models.get.side_effect = api_error("offline")
        assert provider.ensure_model() is False
    assert errors
