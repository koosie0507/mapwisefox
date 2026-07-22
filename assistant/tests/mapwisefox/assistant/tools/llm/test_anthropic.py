from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jinja2

from mapwisefox.assistant.tools.llm._anthropic import (
    AnthropicJSONGenerator,
    AnthropicProvider,
)


class Param(dict):
    pass


def _modules(client=None):
    anthropic = SimpleNamespace(
        transform_schema=MagicMock(side_effect=lambda schema: schema),
        Anthropic=MagicMock(return_value=client),
        APIError=type("APIError", (Exception,), {}),
    )
    beta = SimpleNamespace(
        BetaMessageParam=Param,
        BetaThinkingConfigEnabledParam=Param,
        BetaThinkingConfigDisabledParam=Param,
        BetaJSONOutputFormatParam=Param,
    )
    return anthropic, beta


def _patch_modules(client=None):
    anthropic, beta = _modules(client)
    return patch(
        "mapwisefox.assistant.tools.llm._anthropic.try_import",
        side_effect=lambda name: anthropic if name == "anthropic" else beta,
    )


def _stream(events):
    stream = MagicMock()
    stream.__enter__.return_value = events
    stream.__exit__.return_value = False
    return stream


def test_anthropic_generator_streams_thinking_and_text():
    client = MagicMock()
    events = [
        SimpleNamespace(
            type="content_block_delta",
            delta=SimpleNamespace(type="thinking_delta", thinking="think"),
        ),
        SimpleNamespace(
            type="content_block_delta",
            delta=SimpleNamespace(type="text_delta", text='{"ok": true}'),
        ),
        SimpleNamespace(type="message_stop", delta=None),
    ]
    client.beta.messages.stream.return_value = _stream(events)
    thoughts, text = [], []
    with (
        _patch_modules(),
        patch("mapwisefox.assistant.tools.llm._anthropic.time.sleep"),
    ):
        generator = AnthropicJSONGenerator(
            client,
            "model",
            thinking=True,
            on_thinking=thoughts.append,
            on_text=text.append,
        )
        result = generator.generate_json(
            jinja2.Template("system"), {}, "user", {"type": "object"}
        )

    assert result == {"ok": True}
    assert thoughts == ["think"]
    assert "{" in "".join(text)
    assert client.beta.messages.stream.call_args.kwargs["max_tokens"] == 2050


def test_anthropic_generator_supports_unstructured_json_mode():
    client = MagicMock()
    client.beta.messages.stream.return_value = _stream(
        [
            SimpleNamespace(
                type="content_block_delta",
                delta=SimpleNamespace(type="text_delta", text='{"ok": true}'),
            )
        ]
    )
    with _patch_modules():
        generator = AnthropicJSONGenerator(client, "model")
        with patch("mapwisefox.assistant.tools.llm._anthropic.time.sleep"):
            result = generator.generate_json(jinja2.Template("system"), {}, "user")

    assert result == {"ok": True}
    assert client.beta.messages.stream.call_args.kwargs["output_format"] is None


def test_anthropic_provider_ensures_model_and_handles_api_error():
    client = MagicMock()
    api_error = type("APIError", (Exception,), {})
    anthropic, beta = _modules(client)
    anthropic.APIError = api_error
    with patch(
        "mapwisefox.assistant.tools.llm._anthropic.try_import",
        side_effect=lambda name: anthropic if name == "anthropic" else beta,
    ):
        provider = AnthropicProvider("model", "key", on_error=lambda *args: None)
        client.models.retrieve.return_value = object()
        assert provider.ensure_model() is True
        client.models.retrieve.side_effect = api_error("offline")
        assert provider.ensure_model() is False
