import pytest

from mapwisefox.assistant.tools.extras import try_import


def test_try_import_returns_imported_module():
    assert try_import("json").__name__ == "json"


def test_try_import_reports_missing_module(monkeypatch):
    def missing(_):
        raise ModuleNotFoundError("missing", name="missing")

    monkeypatch.setattr("mapwisefox.assistant.tools.extras.import_module", missing)

    with pytest.raises(ImportError, match="'missing' is not installed"):
        try_import("missing")


def test_try_import_includes_extra_name_in_error(monkeypatch):
    def missing(_):
        raise ModuleNotFoundError("missing", name="missing")

    monkeypatch.setattr("mapwisefox.assistant.tools.extras.import_module", missing)

    with pytest.raises(ImportError, match="'pdf' extra"):
        try_import("missing", extra="pdf")


def test_try_import_reraises_nested_missing_dependency(monkeypatch):
    def nested(_):
        raise ModuleNotFoundError("nested", name="nested")

    monkeypatch.setattr("mapwisefox.assistant.tools.extras.import_module", nested)

    with pytest.raises(ModuleNotFoundError):
        try_import("available")
