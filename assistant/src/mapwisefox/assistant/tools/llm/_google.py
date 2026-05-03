import io
import os
from typing import TYPE_CHECKING, Optional

from mapwisefox.assistant.tools.extras import try_import
from mapwisefox.assistant.tools.llm._provider import LLMProviderBase, JSONGenerator

if TYPE_CHECKING:
    import google.genai as genai


class GoogleJSONGenerator(JSONGenerator):
    def __init__(
        self,
        client: "genai.Client",
        model_name: str,
        max_retries: int = 1,
        thinking_level: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            kwargs.pop("on_error", None),
            kwargs.pop("on_thinking", None),
            kwargs.pop("on_text", None),
        )
        self.__client: "genai.Client" = client
        self.__model_name = model_name
        self.__max_retries = max_retries
        self.__thinking_cfg = self._get_thinking_config(thinking_level)

    def _get_thinking_config(self, thinking_level: Optional[str]) -> dict:
        if thinking_level is None:
            return {"include_thoughts": False}
        result: dict = {"include_thoughts": True}
        if "flash" not in self.__model_name:
            result["thinking_level"] = thinking_level
        return result

    @staticmethod
    def _get_schema(response_format: str | dict) -> Optional[dict]:
        if not isinstance(response_format, dict):
            return None
        return response_format

    def _generate_text(
        self, system_prompt: str, user_prompt: str, response_format: str | dict
    ) -> str:
        try:
            output_format = self._get_schema(response_format)
            buf = io.StringIO()
            thoughts = False
            stream = None
            retries = self.__max_retries
            while stream is None and retries > 0:
                stream = self.__client.models.generate_content_stream(
                    model=self.__model_name,
                    contents=user_prompt,
                    config={
                        "system_instruction": system_prompt,
                        "response_mime_type": "application/json",
                        "response_json_schema": output_format,
                        "thinking_config": self.__thinking_cfg,
                    },
                )
                retries -= 1

            for chunk in stream:
                if chunk.candidates[0].content.parts is None:
                    continue
                for part in chunk.candidates[0].content.parts:
                    if not part.text:
                        continue
                    elif part.thought:
                        self._thinking_callback(part.text)
                        thoughts = True
                    else:
                        buf.write(part.text)
                        if thoughts:
                            self._text_callback(os.linesep)
                            thoughts = False
                        self._text_callback(part.text)
            self._text_callback(os.linesep)
            return buf.getvalue()
        except Exception as e:
            self._error_callback("something went horribly wrong", e)
            return ""


class GoogleProvider(LLMProviderBase):
    def __new__(cls, *args, **kwargs):
        proto = super().__new__(cls)
        proto.Client = try_import("google.genai").Client
        proto.APIError = try_import("google.genai.errors").APIError
        return proto

    def __init__(self, model: str, api_key: str, **kwargs):
        super().__init__(
            model,
            kwargs.pop("on_error", None),
            kwargs.pop("on_thinking", None),
            kwargs.pop("on_text", None),
        )
        self.__client: "genai.Client" = self.Client(api_key=api_key)

    def ensure_model(self) -> bool:
        try:
            model = self.__client.models.get(model=self._model_name)
            return model is not None
        except (ValueError, self.APIError) as err:
            self._error_callback("error loading Google AI model", err)
            return False

    def new_json_generator(
        self, max_retries: int = 3, thinking: str = "low"
    ) -> GoogleJSONGenerator:
        return GoogleJSONGenerator(
            self.__client,
            self._model_name,
            max_retries,
            thinking,
            on_error=self._error_callback,
            on_thinking=self._thinking_callback,
            on_text=self._text_callback,
        )
