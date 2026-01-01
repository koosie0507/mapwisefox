import io
import os
from typing import TYPE_CHECKING

import openai

from mapwisefox.assistant.tools.extras import try_import
from mapwisefox.assistant.tools.llm._provider import LLMProviderBase, JSONGenerator


class OpenAIJSONGenerator(JSONGenerator):
    if TYPE_CHECKING:
        import openai
        import openai.types.responses

    def __init__(
        self,
        client: "openai.OpenAI",
        model_name: str,
        max_retries: int = 1,
        thinking: str = "low",
        **kwargs,
    ) -> None:
        super().__init__(
            kwargs.pop("on_error", None),
            kwargs.pop("on_thinking", None),
            kwargs.pop("on_text", None),
        )
        self.__client: openai.OpenAI = client
        self.__model_name = model_name
        self.__max_retries = max_retries
        self.__thinking = thinking
        self.__schema_param = try_import(
            "openai.types.responses"
        ).ResponseFormatTextJSONSchemaConfigParam

    def _generate_text(
        self, system_prompt: str, user_prompt: str, response_format: str | dict
    ) -> str:
        openai_format = (
            {"type": "json_object"}
            if isinstance(response_format, str)
            else self.__schema_param(
                type="json_schema",
                json_schema={
                    "name": "response-schema",
                    "schema": response_format,
                },
            )
        )
        buf = io.StringIO()
        try:
            with self.__client.responses.stream(
                model=self.__model_name,
                instructions=system_prompt,
                input=user_prompt,
                text_format=openai_format,
                reasoning={"effort": self.__thinking},
            ) as response:
                for event in response:
                    if event.type not in {
                        "response.created",
                        "response.output_text.delta",
                        "response.completed",
                        "error",
                    }:
                        continue
                    if event.type == "response.output_text.delta":
                        self._text_callback(event.delta)
                        buf.write(event.delta)
                    if event.type == "response.completed":
                        self._text_callback("\n")
                    if event.type == "error":
                        self._error_callback("", ValueError(""))
            self._text_callback(os.linesep)
        except TypeError:
            pass

        return buf.getvalue()


class OpenAIProvider(LLMProviderBase):
    """Factory that returns Ollama clients for various tasks."""

    def __init__(self, model: str, api_key: str, **kwargs):
        super().__init__(
            model,
            kwargs.pop("on_error", None),
            kwargs.pop("on_thinking", None),
            kwargs.pop("on_text", None),
        )
        self.__client = try_import("openai").OpenAI(api_key=api_key)

    def new_json_generator(
        self, max_retries: int = 1, thinking: str = "low"
    ) -> OpenAIJSONGenerator:
        return OpenAIJSONGenerator(
            self.__client,
            self._model_name,
            max_retries,
            thinking,
            on_error=self._error_callback,
            on_thinking=self._thinking_callback,
            on_text=self._text_callback,
        )
