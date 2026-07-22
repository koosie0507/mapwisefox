import jinja2
import pytest
from itertools import repeat

from mapwisefox.assistant.tools.llm._provider import JSONGenerator, LLMProviderBase


class FakeGenerator(JSONGenerator):
    def __init__(self, responses, **kwargs):
        super().__init__(**kwargs)
        self.responses = iter(responses)

    def _generate_text(self, system_prompt, user_prompt, response_format):
        return next(self.responses)


class FakeProvider(LLMProviderBase):
    def ensure_model(self):
        return True

    def new_json_generator(self, max_retries=1, thinking=False):
        return FakeGenerator(["{}"], max_retries=max_retries)


def test_json_generator_renders_prompt_and_parses_json():
    generator = FakeGenerator(['{"answer": "include"}'])

    result = generator.generate_json(
        jinja2.Template("topic={{ topic }}"),
        {"topic": "SLR"},
        "paper text",
    )

    assert result == {"answer": "include"}


def test_json_generator_strips_json_code_fence():
    generator = FakeGenerator(['```json\n{"answer": "include"}\n```'])

    result = generator.generate_json(jinja2.Template("prompt"), {}, "paper")

    assert result["answer"] == "include"


def test_json_generator_passes_schema_to_text_generator():
    class CapturingGenerator(FakeGenerator):
        def _generate_text(self, system_prompt, user_prompt, response_format):
            self.response_format = response_format
            return "{}"

    generator = CapturingGenerator(["{}"])
    schema = {"type": "object"}

    generator.generate_json(jinja2.Template("prompt"), {}, "paper", schema)

    assert generator.response_format == schema


def test_json_generator_retries_json_decode_errors_and_calls_error_callback():
    errors = []
    generator = FakeGenerator(
        ["not json", '{"ok": true}'],
        max_retries=2,
        on_error=lambda message, error: errors.append(message),
    )

    result = generator.generate_json(jinja2.Template("prompt"), {}, "paper")

    assert result == {"ok": True}
    assert len(errors) == 1


def test_json_generator_retries_value_errors():
    class ValueErrorGenerator(FakeGenerator):
        def _generate_text(self, system_prompt, user_prompt, response_format):
            if not hasattr(self, "called"):
                self.called = True
                raise ValueError("temporary failure")
            return '{"ok": true}'

    generator = ValueErrorGenerator(["unused"], max_retries=2)

    assert generator.generate_json(jinja2.Template("prompt"), {}, "paper") == {
        "ok": True
    }


def test_json_generator_raises_after_retries_are_exhausted():
    generator = FakeGenerator(repeat("not json"), max_retries=2)

    with pytest.raises(ValueError, match="non-JSON"):
        generator.generate_json(jinja2.Template("prompt"), {}, "paper")


def test_llm_provider_base_stores_model_and_is_abstract():
    FakeProvider("model")

    with pytest.raises(TypeError):
        LLMProviderBase("model")
