from dataclasses import dataclass, field
from enum import StrEnum


class ModelChoice(StrEnum):
    ministral = "ministral-3:14b"
    qwen3_vl = "qwen3-vl:8b"
    gpt = "gpt-oss:20b"
    deepseek = "deepseek-r1:14b"
    llama = "llama3.1:8b"
    qwen3 = "qwen3:8b"


@dataclass
class AssistantParams:
    model_choice: ModelChoice = field(init=True, repr=True, default=ModelChoice.gpt)
    ollama_host: str = field(init=True, repr=True, default="localhost")
    ollama_port: int = field(init=True, repr=True, default=11434)
