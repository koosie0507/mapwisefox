import io
import os
from typing import Optional, TYPE_CHECKING

from mapwisefox.assistant.tools.extras import try_import
from mapwisefox.assistant.tools.llm._provider import LLMProviderBase, JSONGenerator

if TYPE_CHECKING:
    import ollama


class OllamaJSONGenerator(JSONGenerator):
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

    def __new__(cls, *args, **kwargs):
        proto = super().__new__(cls)
        ollama_module = try_import("ollama")
        proto.Client = ollama_module.Client
        proto.RequestError = ollama_module.RequestError
        proto.ResponseError = ollama_module.ResponseError
        return proto

    def __init__(self, model: str, ollama_host: Optional[str] = None, **kwargs):
        super().__init__(
            model,
            kwargs.pop("on_error", None),
            kwargs.pop("on_thinking", None),
            kwargs.pop("on_text", None),
        )
        self.__client = self.Client(host=ollama_host)

    def _download_model(self) -> bool:
        try:
            digest = ""
            total = None
            step_size = 0
            bucket = 0
            for progress in self.__client.pull(self._model_name, stream=True):
                if (
                    current_digest := progress.get("digest")
                ) is not None and current_digest != digest:
                    digest = current_digest

                completed = progress.get("completed", 0) or 0
                if (bucket == 0 and step_size == 0) or (
                    step_size != 0 and (completed // step_size) > bucket
                ):
                    status = progress.get("status", "<unkown status>")
                    self._text_callback(
                        f"Download {self._model_name} progress [{completed}/{total}]: {status}{os.linesep}"
                    )
                    if step_size != 0:
                        bucket += 1

                if (
                    current_total := progress.get("total")
                ) is not None and total != current_total:
                    total = current_total
                    step_size = total // 20
            return True
        except (self.RequestError, self.ResponseError) as err:
            self._error_callback(f"failed to download model {self._model_name!r}", err)
            return False

    def ensure_model(self) -> bool:
        try:
            local_model_names = set(x.model for x in self.__client.list().models)
        except (self.RequestError, self.ResponseError) as err:
            self._error_callback("unable to fetch Ollama model information", err)
            return False
        if self._model_name in local_model_names:
            return True
        return self._download_model()

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
