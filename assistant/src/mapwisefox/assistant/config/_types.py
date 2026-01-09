from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional, Callable


class ProviderChoice(StrEnum):
    ollama = "ollama"
    openai = "openai"
    anthropic = "anthropic"


class ModelChoice(StrEnum):
    ministral = "ministral-3:14b"
    qwen3_vl = "qwen3-vl:8b"
    gpt_oss = "gpt-oss:20b"
    deepseek = "deepseek-r1:14b"
    llama = "llama3.1:8b"
    qwen3 = "qwen3:8b"
    gpt_52 = "gpt-5.2-2025-12-11"
    gpt_5 = "gpt-5-2025-08-07"
    gpt_5_mini = "gpt-5-mini-2025-08-07"
    sonnet_4_5 = "claude-sonnet-4-5-20250929"
    haiku_4_5 = "claude-haiku-4-5-20251001"
    opus_4_5 = "claude-opus-4-5-20251101"


class ReaderType(StrEnum):
    docling = "docling"
    custom = "custom"


@dataclass
class AssistantParams:
    provider_factory: Optional[Callable] = field(init=True, repr=True, default=None)
    model_choice: ModelChoice = field(init=True, repr=True, default=ModelChoice.gpt_oss)
    ollama_host: str = field(init=True, repr=True, default="localhost")
    ollama_port: int = field(init=True, repr=True, default=11434)
    api_key: Optional[str] = field(init=True, repr=True, default=None)
