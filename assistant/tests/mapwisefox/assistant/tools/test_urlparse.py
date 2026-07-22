from pathlib import Path

import pytest

from mapwisefox.assistant.tools.urlparse import UrlInfo


def test_url_info_exposes_http_scheme():
    assert UrlInfo("https://example.com/paper.pdf").scheme == "https"


@pytest.mark.parametrize(
    "uri", ["file:///tmp/paper.pdf", "file://localhost/tmp/paper.pdf"]
)
def test_url_info_resolves_local_file(uri):
    assert UrlInfo(uri).local_path == Path("/tmp/paper.pdf").resolve()


def test_url_info_rejects_non_local_path_access():
    with pytest.raises(ValueError, match="does not describe a local file"):
        UrlInfo("https://example.com/paper.pdf").local_path
