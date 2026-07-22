from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jinja2

from mapwisefox.assistant.tools.llm._ollama import OllamaJSONGenerator, OllamaProvider


def _chunk(thinking="", content=""):
    return SimpleNamespace(message=SimpleNamespace(thinking=thinking, content=content))


def test_ollama_generator_streams_thoughts_and_text():
    client = MagicMock()
    client.chat.return_value = iter(
        [
            _chunk(thinking="thinking"),
            _chunk(content='{"ok":'),
            _chunk(content=" true}"),
        ]
    )
    thoughts, text = [], []
    generator = OllamaJSONGenerator(
        client,
        "llama",
        on_thinking=thoughts.append,
        on_text=text.append,
    )

    result = generator.generate_json(jinja2.Template("system"), {}, "user")

    assert result == {"ok": True}
    assert thoughts == ["thinking"]
    assert "{" in "".join(text)
    client.chat.assert_called_once()


def test_ollama_provider_ensures_existing_model():
    client = MagicMock()
    client.list.return_value.models = [SimpleNamespace(model="model")]
    module = SimpleNamespace(
        Client=MagicMock(return_value=client),
        RequestError=type("RequestError", (Exception,), {}),
        ResponseError=type("ResponseError", (Exception,), {}),
    )

    with patch(
        "mapwisefox.assistant.tools.llm._ollama.try_import", return_value=module
    ):
        provider = OllamaProvider(
            "model",
            "localhost",
            on_error=lambda *args: None,
            on_text=lambda *args: None,
        )

    assert provider.ensure_model() is True
    client.pull.assert_not_called()


def test_ollama_provider_downloads_missing_model():
    client = MagicMock()
    client.list.return_value.models = []
    client.pull.return_value = iter(
        [{"status": "done", "total": 100, "completed": 100}]
    )
    module = SimpleNamespace(
        Client=MagicMock(return_value=client),
        RequestError=type("RequestError", (Exception,), {}),
        ResponseError=type("ResponseError", (Exception,), {}),
    )

    with patch(
        "mapwisefox.assistant.tools.llm._ollama.try_import", return_value=module
    ):
        provider = OllamaProvider("model", "localhost", on_text=lambda *args: None)

    assert provider.ensure_model() is True
    client.pull.assert_called_once_with("model", stream=True)


def test_ollama_provider_returns_false_on_model_service_error():
    request_error = type("RequestError", (Exception,), {})
    client = MagicMock()
    client.list.side_effect = request_error("offline")
    errors = []
    module = SimpleNamespace(
        Client=MagicMock(return_value=client),
        RequestError=request_error,
        ResponseError=type("ResponseError", (Exception,), {}),
    )

    with patch(
        "mapwisefox.assistant.tools.llm._ollama.try_import", return_value=module
    ):
        provider = OllamaProvider(
            "model",
            "localhost",
            on_error=lambda msg, err: errors.append(msg),
            on_text=lambda *args: None,
        )

    assert provider.ensure_model() is False
    assert errors


def test_ollama_provider_returns_false_when_download_fails():
    response_error = type("ResponseError", (Exception,), {})
    client = MagicMock()
    client.list.return_value.models = []
    client.pull.side_effect = response_error("failed")
    module = SimpleNamespace(
        Client=MagicMock(return_value=client),
        RequestError=type("RequestError", (Exception,), {}),
        ResponseError=response_error,
    )

    with patch(
        "mapwisefox.assistant.tools.llm._ollama.try_import", return_value=module
    ):
        provider = OllamaProvider(
            "model",
            "localhost",
            on_error=lambda *args: None,
            on_text=lambda *args: None,
        )

    assert provider.ensure_model() is False
