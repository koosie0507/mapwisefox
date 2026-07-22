from unittest.mock import MagicMock

import pytest
import requests

from mapwisefox.assistant.tools.fileprovider import FileProvider


@pytest.fixture
def mock_get(monkeypatch):
    response = MagicMock()
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    response.headers = {"Content-Type": "application/pdf"}
    response.iter_content.return_value = [b"%PDF-1.4 fake pdf bytes"]
    response.raise_for_status.return_value = None
    get = MagicMock(return_value=response)
    monkeypatch.setattr(requests.Session, "get", get)
    return get


def test_file_provider_verifies_tls_by_default(tmp_path, mock_get):
    provider = FileProvider(tmp_path)

    provider("https://example.com/paper.pdf")

    assert mock_get.call_args.kwargs["verify"] is True


def test_file_provider_can_disable_tls_verification(tmp_path, mock_get):
    provider = FileProvider(tmp_path, verify_tls=False)

    provider("https://example.com/paper.pdf")

    assert mock_get.call_args.kwargs["verify"] is False


def test_file_provider_rejects_cache_path_that_is_a_file(tmp_path):
    cache_file = tmp_path / "cache"
    cache_file.write_text("not a directory")

    with pytest.raises(ValueError, match="not a directory"):
        FileProvider(cache_file)


def test_file_provider_returns_local_file_without_download(tmp_path, mock_get):
    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"pdf")

    assert FileProvider(tmp_path)(f"file://{paper}") == paper.resolve()
    mock_get.assert_not_called()


def test_file_provider_rejects_unsupported_scheme(tmp_path):
    with pytest.raises(ValueError, match="scheme"):
        FileProvider(tmp_path)("ftp://example.com/paper.pdf")


def test_file_provider_rejects_non_pdf_content(tmp_path, mock_get):
    mock_get.return_value.headers = {"Content-Type": "text/html"}

    with pytest.raises(ValueError, match="content type"):
        FileProvider(tmp_path)("https://example.com/paper.pdf")


def test_file_provider_redownloads_when_cached_hash_is_stale(tmp_path, mock_get):
    provider = FileProvider(tmp_path)
    url = "https://example.com/paper.pdf"
    local_path = provider(url)
    local_path.write_bytes(b"old")
    local_path.with_name(f"{local_path.name}.sha256").write_text("wrong")

    provider(url)

    assert mock_get.called
