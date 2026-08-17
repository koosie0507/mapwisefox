from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional, Callable


class ProviderChoice(StrEnum):
    ollama = "ollama"
    openai = "openai"
    anthropic = "anthropic"
    google = "google"
    bedrock = "aws-bedrock"


class ReaderType(StrEnum):
    docling = "docling"
    custom = "custom"


@dataclass
class AssistantParams:
    provider_factory: Optional[Callable] = field(init=True, repr=True, default=None)
    model_choice: str = field(init=True, repr=True, default="gpt-oss:20b")
    ollama_endpoint: str = field(init=True, repr=True, default="http://localhost:11434")
    api_key: Optional[str] = field(init=True, repr=True, default=None)
