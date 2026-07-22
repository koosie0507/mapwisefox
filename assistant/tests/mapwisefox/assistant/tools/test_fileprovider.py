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
