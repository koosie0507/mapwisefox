import json
import re
from abc import ABC, abstractmethod
from typing import Optional, Any

import jinja2

from mapwisefox.assistant.tools.llm import ErrorCallback, TextCallback


class JSONGenerator(ABC):
    @staticmethod
    def _no_op(*_, **__):
        pass

    def __init__(
        self,
        on_error: Optional[ErrorCallback] = None,
        on_thinking: Optional[TextCallback] = None,
        on_text: Optional[TextCallback] = None,
        max_retries: int = 1,
    ) -> None:
        self._error_callback = on_error or self._no_op
        self._thinking_callback = on_thinking or self._no_op
        self._text_callback = on_text or self._no_op
        self.__max_retries = max_retries

    @abstractmethod
    def _generate_text(
        self, system_prompt: str, user_prompt: str, response_format: str | dict
    ) -> str:
        pass

    def generate_json(
        self,
        system_prompt_template: jinja2.Template,
        template_data: dict[str, Any],
        user_prompt: str,
        response_schema: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        answered = False
        answer_text = ""
        answer_obj: dict[str, Any] = {}
        attempts = self.__max_retries

        while not answered and attempts > 0:
            try:
                system_prompt = system_prompt_template.render(**template_data)
                answer_text = re.sub(
                    r"`+\w*[\s$]*(\{.+\})[$\s]*`+",
                    r"\1",
                    self._generate_text(
                        system_prompt, user_prompt, response_schema or "json"
                    ),
                )
                answer_obj = json.loads(answer_text)
                answered = True
            except json.JSONDecodeError as err:
                self._error_callback(
                    f"decoding LLM answer as JSON failed; {attempts} retries left", err
                )
            except ValueError as err:
                self._error_callback(
                    f"value error while generating text; {attempts} retries left", err
                )
            finally:
                attempts -= 1

        if not answered and attempts == 0:
            raise ValueError(f"LLM answered non-JSON value: {answer_text!r}")

        return answer_obj


class LLMProviderBase(ABC):
    def __init__(
        self,
        model: str,
        on_error: Optional[ErrorCallback] = None,
        on_thinking: Optional[ErrorCallback] = None,
        on_text: Optional[ErrorCallback] = None,
    ) -> None:
        self._model_name = model
        self._error_callback = on_error
        self._thinking_callback = on_thinking
        self._text_callback = on_text

    @abstractmethod
    def new_json_generator(
        self, max_retries: int = 1, thinking: bool = False
    ) -> JSONGenerator:
        pass
