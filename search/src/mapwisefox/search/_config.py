"""Configuration schema for the `search` CLI entry point."""

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from mapwisefox.search import backends as backends_pkg
from mapwisefox.search.backends import (
    ConsoleBackend,
    SearchBackend,
    WebOfScienceBackend,
)
from mapwisefox.search.dsl import adapters as adapters_pkg
from mapwisefox.search.dsl.adapters import DSLAdapter


# Every concrete adapter/backend exported by the respective packages is
# addressable by name from the config file. The abstract base classes are
# deliberately excluded since they can't be used on their own.
_ADAPTERS: dict[str, type[DSLAdapter]] = {
    name: getattr(adapters_pkg, name)
    for name in adapters_pkg.__all__
    if name != "DSLAdapter"
}
_BACKENDS: dict[str, type[SearchBackend]] = {
    name: getattr(backends_pkg, name)
    for name in backends_pkg.__all__
    if name != "SearchBackend"
}


class BackendRef(BaseModel):
    """Which backend class to instantiate, and the options to build it with."""

    type: str
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type")
    @classmethod
    def _known_backend(cls, value: str) -> str:
        if value not in _BACKENDS:
            raise ValueError(
                f"unknown backend {value!r}; available backends: "
                f"{sorted(_BACKENDS)}"
            )
        return value

    @property
    def backend_cls(self) -> type[SearchBackend]:
        return _BACKENDS[self.type]


class BackendSpec(BaseModel):
    """A single backend to run a parsed DSL query against."""

    name: str
    adapter: str
    backend: BackendRef
    adapter_options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("backend", mode="before")
    @classmethod
    def _normalize_backend(cls, value: Any) -> Any:
        """Allow ``backend: SomeBackend`` as shorthand for
        ``backend: {type: SomeBackend}`` when no options are needed."""
        if isinstance(value, str):
            return {"type": value}
        return value

    @field_validator("adapter")
    @classmethod
    def _known_adapter(cls, value: str) -> str:
        if value not in _ADAPTERS:
            raise ValueError(
                f"unknown adapter {value!r}; available adapters: "
                f"{sorted(_ADAPTERS)}"
            )
        return value

    @property
    def adapter_cls(self) -> type[DSLAdapter]:
        return _ADAPTERS[self.adapter]

    @property
    def backend_cls(self) -> type[SearchBackend]:
        return self.backend.backend_cls

    @property
    def backend_options(self) -> dict[str, Any]:
        return self.backend.options

    @property
    def is_console_backend(self) -> bool:
        return issubclass(self.backend_cls, ConsoleBackend) or (
            issubclass(self.backend_cls, WebOfScienceBackend)
            and not self.backend.options.get("use_starter_api", False)
        )


class SearchConfig(BaseModel):
    """Top-level search configuration file schema."""

    query: str | None = None
    query_file: str | None = None
    backends: list[BackendSpec] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_query_and_backend_names(self) -> "SearchConfig":
        if bool(self.query) == bool(self.query_file):
            raise ValueError(
                "config must specify exactly one of 'query' or 'query_file'"
            )
        names = [b.name for b in self.backends]
        if len(names) != len(set(names)):
            raise ValueError("backend names must be unique")
        return self
