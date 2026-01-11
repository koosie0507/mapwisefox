import io
import json
import os
from datetime import timedelta
from functools import partial
from typing import TYPE_CHECKING, Generator, Optional

from tenacity import (
    retry,
    retry_if_exception,
    wait_random_exponential,
    stop_after_delay,
)

from mapwisefox.assistant.config import ModelChoice
from mapwisefox.assistant.tools.extras import try_import
from mapwisefox.assistant.tools.llm._provider import LLMProviderBase, JSONGenerator

if TYPE_CHECKING:
    import botocore
    import botocore.client
    import botocore.exceptions


def _is_throttling_exception(err: BaseException) -> bool:
    if not hasattr(err, "response"):
        return False
    response = getattr(err, "response")
    return response.get("Error", {}).get("Code") == "ThrottlingException"


class BedrockJSONGenerator(JSONGenerator):
    def __init__(
        self,
        client: "botocore.client.BaseClient",
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
        self.__thinking = thinking
        self.__request_body_factories = [
            (lambda: "anthropic." in self.__model_name, self._anthropic_request_body),
            (lambda: "openai." in self.__model_name, self._openai_request_body),
        ]
        self.__event_obj_processors = [
            (
                lambda: "anthropic." in self.__model_name,
                self._process_anthropic_event_obj,
            ),
            (lambda: "openai." in self.__model_name, self._process_openai_event_obj),
        ]

    @staticmethod
    def _create_formatting_prompt(response_format: str | dict) -> str:
        if isinstance(response_format, dict):
            json_schema = json.dumps(response_format, indent=2)
            return f"""OUTPUT ONLY JSON. MUST JSON Schema:\n{json_schema}\n-----\n"""
        return "OUTPUT ONLY JSON\n-----\n"

    def _openai_request_body(
        self, response_format: str | dict, system_prompt: str, user_prompt: str
    ) -> str:
        response_format = (
            {
                "type": "json_schema",
                "json_schema": {
                    "name": "Response",
                    "description": "format of the response",
                    "schema": response_format,
                    "strict": True,
                },
            }
            if isinstance(response_format, dict)
            else {"type": "json_object"}
        )
        request_body = json.dumps(
            {
                "model": self.__model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "reasoning_effort": "medium" if self.__thinking else "low",
                "response_format": response_format,
                "top_p": 0.2,
            }
        )
        return request_body

    @staticmethod
    def _anthropic_request_body(
        response_format: str | dict, system_prompt: str, user_prompt: str
    ) -> str:
        system_text = system_prompt + BedrockJSONGenerator._create_formatting_prompt(
            response_format
        )
        request_body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": user_prompt}],
                "system": system_text,
            }
        )
        return request_body

    def __create_request_body(
        self, response_format: str | dict, system_prompt: str, user_prompt: str
    ) -> str:
        for condition, factory in self.__request_body_factories:
            if not condition():
                continue
            return factory(response_format, system_prompt, user_prompt)
        raise ValueError(
            f"no idea how to handle requests for model {self.__model_name}"
        )

    @retry(
        wait=wait_random_exponential(multiplier=1, max=60),
        retry=retry_if_exception(_is_throttling_exception),
        stop=stop_after_delay(timedelta(seconds=120)),
    )
    def _perform_request(
        self, response_format: str | dict, system_prompt: str, user_prompt: str
    ) -> Optional[Generator]:
        request_body = self.__create_request_body(
            response_format, system_prompt, user_prompt
        )

        response = self.__client.invoke_model_with_response_stream(
            modelId=self.__model_name,
            body=request_body,
            contentType="application/json",
            accept="application/json",
        )
        return response.get("body")

    def _process_openai_event_obj(
        self, buf: io.StringIO, event_obj: dict, currently_thinking: bool
    ) -> bool:
        choices = event_obj.get("choices", [])
        if not (isinstance(choices, list) and len(choices) > 0):
            return currently_thinking
        choice = choices[0]
        if not (delta := str(choice.get("delta", {}).get("content", ""))):
            return currently_thinking
        if "<reasoning>" in delta:
            self._thinking_callback(
                delta.removeprefix("<reasoning>").removesuffix("</reasoning>")
            )
            return True

        if len(delta) == 0:
            return currently_thinking

        if currently_thinking:
            self._text_callback(os.linesep)
            currently_thinking = False
        # weird error returned only on bedrock
        if delta.startswith('{"{'):
            delta = delta[2:]
        buf.write(delta)
        self._text_callback(delta)

        return currently_thinking

    def _process_anthropic_event_obj(
        self, buf: io.StringIO, event_obj: dict, currently_thinking: bool
    ) -> bool:
        if event_obj.get("type") != "content_block_delta":
            return currently_thinking
        if not (delta := event_obj.get("delta")):
            return currently_thinking
        delta_type = delta.get("type")
        if delta_type is None:
            return currently_thinking

        if delta_type == "thinking_delta":
            self._thinking_callback(delta.get("thinking"))
            return True
        elif delta_type == "text_delta":
            if not (chunk_text := delta.get("text")):
                return currently_thinking
            buf.write(chunk_text)
            if currently_thinking:
                self._text_callback(os.linesep)
                currently_thinking = False
            self._text_callback(chunk_text)

        return currently_thinking

    def __process_event_obj(
        self, buf: io.StringIO, event_obj: dict, currently_thinking: bool
    ):
        for condition, processor in self.__event_obj_processors:
            if not condition():
                continue
            return processor(buf, event_obj, currently_thinking)
        raise ValueError(
            f"no idea how to handle requests for model {self.__model_name}"
        )

    def _process_stream(self, stream: Generator) -> str:
        buf = io.StringIO()
        thoughts = False
        for event in stream:
            if not (chunk := event.get("chunk")):
                continue
            if not (chunk_data := chunk.get("bytes")):
                continue
            event_obj = json.loads(chunk_data)
            thoughts = self.__process_event_obj(buf, event_obj, thoughts)

        self._text_callback(os.linesep)
        result = buf.getvalue().strip()
        valid_json_opener = result.index("{")
        if valid_json_opener > 0:
            result = result[valid_json_opener:]

        valid_json_closer = result.rindex("}")
        if valid_json_closer < len(result) - 1:
            result = result[: valid_json_closer + 1]
        return result

    def _generate_text(
        self, system_prompt: str, user_prompt: str, response_format: str | dict
    ) -> str:
        stream = self._perform_request(response_format, system_prompt, user_prompt)
        if not stream:
            return ""
        result = self._process_stream(stream)
        return result


class BedrockProvider(LLMProviderBase):
    MODEL_MAPPING = {
        ModelChoice.haiku_4_5.value: "anthropic.claude-3-haiku-20240307-v1:0",
        ModelChoice.sonnet_4_5.value: "anthropic.claude-sonnet-4-5-20250929-v1:0",
        ModelChoice.opus_4_5.value: "anthropic.claude-opus-4-5-20251101-v1:0",
        ModelChoice.gpt_oss: "openai.gpt-oss-20b-1:0",
        ModelChoice.gpt_oss_120b: "openai.gpt-oss-120b-1:0",
    }

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        if not hasattr(cls, "_guard") or not getattr(cls, "_guard"):
            boto3_module = try_import("boto3")
            obj.Bedrock = partial(boto3_module.client, "bedrock")
            obj.BedrockClient = partial(boto3_module.client, "bedrock-runtime")
            exceptions_module = try_import("botocore.exceptions")
            obj.ClientError = exceptions_module.ClientError
            obj.BotoCoreError = exceptions_module.BotoCoreError
            obj.needs_region_prefix = kwargs.get("model") in {
                ModelChoice.haiku_4_5,
                ModelChoice.sonnet_4_5,
                ModelChoice.opus_4_5,
            }
            cls._guard = True
        return obj

    def __init__(self, model: str, api_key: str, **kwargs):
        super().__init__(
            self.MODEL_MAPPING.get(model, model),
            kwargs.pop("on_error", None),
            kwargs.pop("on_thinking", None),
            kwargs.pop("on_text", None),
        )
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = api_key
        self.__bedrock = self.Bedrock()
        self.__runtime_client = self.BedrockClient()

    def ensure_model(self) -> bool:
        try:
            model_info = self.__bedrock.get_foundation_model(
                modelIdentifier=self._model_name
            )
            return model_info is not None
        except (self.BotoCoreError, self.ClientError) as err:
            self._error_callback(
                "unable to fetch information about Anthropic model", err
            )
            return False

    def new_json_generator(
        self, max_retries: int = 1, thinking: bool = False
    ) -> BedrockJSONGenerator:
        return BedrockJSONGenerator(
            self.__runtime_client,
            f"eu.{self._model_name}" if self.needs_region_prefix else self._model_name,
            max_retries,
            on_error=self._error_callback,
            on_thinking=self._thinking_callback,
            on_text=self._text_callback,
        )
