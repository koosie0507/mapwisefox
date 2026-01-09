import io
import time
from typing import Optional, TYPE_CHECKING, Any

from pydantic import create_model

from mapwisefox.assistant.tools.extras import try_import
from mapwisefox.assistant.tools.llm._provider import LLMProviderBase, JSONGenerator

if TYPE_CHECKING:
    import anthropic
    import anthropic.types.beta as beta


class AnthropicJSONGenerator(JSONGenerator):
    def __new__(cls, *args, **kwargs):
        proto = object.__new__(cls)

        anthropic_module = try_import("anthropic")
        proto._transform_schema = anthropic_module.transform_schema
        beta_module = try_import("anthropic.types.beta")
        proto._BetaMessageParam = beta_module.BetaMessageParam
        proto._BetaThinkingEnabled = beta_module.BetaThinkingConfigEnabledParam
        proto._BetaThinkingDisabled = beta_module.BetaThinkingConfigDisabledParam
        proto._BetaOutputParam = beta_module.BetaJSONOutputFormatParam

        return proto

    def __init__(
        self,
        client: "anthropic.Anthropic",
        model_name: str,
        max_retries: int = 1,
        thinking: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            kwargs.pop("on_error", None),
            kwargs.pop("on_thinking", None),
            kwargs.pop("on_text", None),
        )
        self.__client = client
        self.__model_name = model_name
        self.__max_retries = max_retries
        self.__thinking = self._new_thinking_obj(thinking)

    def _new_thinking_obj(self, thinking: bool) -> "beta.BetaThinkingConfigEnabledParam|beta.BetaThinkingConfigDisabledParam":
        return self._BetaThinkingEnabled(
            type="enabled", budget_tokens=1025
        ) if thinking else self._BetaThinkingDisabled(type="disabled")

    @staticmethod
    def _json_schema_to_pydantic(schema: dict, model_name: str = "MessageResponse"):
        fields = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        for field_name, field_schema in properties.items():
            field_type = type_mapping.get(field_schema.get("type"), Any)
            is_required = field_name in required

            if is_required:
                fields[field_name] = (field_type, ...)
            else:
                fields[field_name] = (Optional[field_type], None)

        return create_model(model_name, **fields)

    def _new_output_format_obj(self, response_format: str | dict) -> Optional["beta.BetaJSONOutputFormatParam"]:
        if not isinstance(response_format, dict):
            return None
        return self._json_schema_to_pydantic(response_format)

    def _generate_text(
        self, system_prompt: str, user_prompt: str, response_format: str | dict
    ) -> str:
        time.sleep(5)
        anthropic_output_format = self._new_output_format_obj(response_format)
        max_tokens = 2050 if self.__thinking else 1024
        prompt = self._BetaMessageParam(role="user", content="\n".join([system_prompt, user_prompt]), )
        with self.__client.beta.messages.stream(
            model=self.__model_name,
            max_tokens=max_tokens,
            betas=["structured-outputs-2025-11-13"],
            messages=[prompt],
            output_format=anthropic_output_format,
            thinking=self.__thinking,
        ) as stream:
            buf = io.StringIO()
            thoughts = False
            for event in stream:
                if event.type != 'content_block_delta':
                    continue
                if event.delta.type == "thinking_delta":
                    self._thinking_callback(event.delta.thinking)
                    thoughts = True
                elif (event.delta.type == "text_delta") and (chunk_text := event.delta.text):
                    buf.write(chunk_text)
                    if thoughts:
                        self._text_callback("\n")
                        thoughts = False
                    self._text_callback(chunk_text)
            self._text_callback("\n")
            return buf.getvalue()


class AnthropicProvider(LLMProviderBase):
    """Factory that returns Ollama clients for various tasks."""

    def __new__(cls, *args, **kwargs):
        proto = super().__new__(cls)
        anthropic_module = try_import("anthropic")
        proto.Anthropic = anthropic_module.Anthropic
        proto.transform_schema = anthropic_module.transform_schema
        proto.APIError = anthropic_module.APIError
        return proto

    def __init__(self,  model: str, api_key: str, **kwargs):
        super().__init__(
            model,
            kwargs.pop("on_error", None),
            kwargs.pop("on_thinking", None),
            kwargs.pop("on_text", None),
        )
        self.__client = self.Anthropic(api_key=api_key)

    def ensure_model(self) -> bool:
        try:
            model_info = self.__client.models.retrieve(self._model_name)
            return model_info is not None
        except self.APIError as err:
            self._error_callback("unable to fetch information about Anthropic model", err)
            return False

    def new_json_generator(
        self, max_retries: int = 1, thinking: bool = False
    ) -> AnthropicJSONGenerator:
        return AnthropicJSONGenerator(
            self.__client,
            self._model_name,
            max_retries,
            thinking,
            on_error=self._error_callback,
            on_thinking=self._thinking_callback,
            on_text=self._text_callback,
        )
