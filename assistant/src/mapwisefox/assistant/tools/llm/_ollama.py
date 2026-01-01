import io
from typing import Optional, TYPE_CHECKING

from mapwisefox.assistant.tools.extras import try_import
from mapwisefox.assistant.tools.llm._provider import LLMProviderBase, JSONGenerator


class OllamaJSONGenerator(JSONGenerator):
    if TYPE_CHECKING:
        import ollama

    def __init__(
        self,
        client: "ollama.Client",
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
        self.__thinking = self._coerce_thinking(thinking, model_name)

    @staticmethod
    def _coerce_thinking(thinking: bool, model_name: str) -> str | bool:
        if "gpt" in model_name:
            return "medium" if thinking else "low"
        return thinking

    def _generate_text(
        self, system_prompt: str, user_prompt: str, response_format: str | dict
    ) -> str:
        response = self.__client.chat(
            model=self.__model_name,
            messages=[
                {
                    "role": "user",
                    "content": "\n".join([system_prompt, user_prompt]),
                }
            ],
            stream=True,
            format=response_format,
            think=self.__thinking,
        )

        buf = io.StringIO()
        thoughts = False
        for chunk in response:
            if chunk.message.thinking:
                self._thinking_callback(chunk.message.thinking)
                thoughts = True
            elif chunk_text := chunk.message.content:
                buf.write(chunk_text)
                if thoughts:
                    self._text_callback("\n")
                    thoughts = False
                self._text_callback(chunk_text)
        self._text_callback("\n")
        return buf.getvalue()


class OllamaProvider(LLMProviderBase):
    """Factory that returns Ollama clients for various tasks."""

    def __init__(self, model: str, ollama_host: Optional[str] = None, **kwargs):
        super().__init__(
            model,
            kwargs.pop("on_error", None),
            kwargs.pop("on_thinking", None),
            kwargs.pop("on_text", None),
        )
        self.__client = try_import("ollama").Client(host=ollama_host)

    def new_json_generator(
        self, max_retries: int = 1, thinking: bool = False
    ) -> OllamaJSONGenerator:
        return OllamaJSONGenerator(
            self.__client,
            self._model_name,
            max_retries,
            thinking,
            on_error=self._error_callback,
            on_thinking=self._thinking_callback,
            on_text=self._text_callback,
        )
