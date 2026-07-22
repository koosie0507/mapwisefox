from unittest.mock import MagicMock

from mapwisefox.assistant.tools.pdf._caching import CachingFileContentsExtractor


def test_caching_extractor_reads_and_writes_cache(tmp_path):
    extractor = MagicMock()
    extractor.read_file.return_value = "paper text"
    caching = CachingFileContentsExtractor(tmp_path, extractor)

    assert caching.read_file(tmp_path / "paper.pdf") == "paper text"
    assert (tmp_path / "paper.txt").read_text() == "paper text"


def test_caching_extractor_uses_existing_cache(tmp_path):
    (tmp_path / "paper.txt").write_text("cached text")
    extractor = MagicMock()
    caching = CachingFileContentsExtractor(tmp_path, extractor)

    assert caching.read_file(tmp_path / "paper.pdf") == "cached text"
    extractor.read_file.assert_not_called()
