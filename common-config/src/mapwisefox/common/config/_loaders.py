import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from mapwisefox.common.config._schemas import QAConfig, SelectionConfig


ConfigModel = TypeVar("ConfigModel", bound=BaseModel)


class ConfigValidationError(ValueError):
    def __init__(self, path: Path, error: ValidationError) -> None:
        super().__init__(f"invalid configuration file {path}:\n{error}")
        self.path = path
        self.errors = error.errors()


def _load_config(path: Path, model: type[ConfigModel]) -> ConfigModel:
    with open(path, "r") as f:
        payload = json.load(f)
    try:
        return model.model_validate(payload)
    except ValidationError as err:
        raise ConfigValidationError(path, err) from err


def load_selection_config(path: Path) -> SelectionConfig:
    return _load_config(path, SelectionConfig)


def load_qa_config(path: Path) -> QAConfig:
    return _load_config(path, QAConfig)
