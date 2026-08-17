from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest
import responses


@pytest.fixture
def sample_pdf_path():
    path = Path(__file__).parents[3] / "data" / "sample.pdf"
    assert path.exists(), f"sample PDF not found at {path}"
    yield path


@pytest.fixture
def paper_url():
    return "https://papers.example.test/sample.pdf"


@pytest.fixture
def example_selection_config_path():
    path = Path(__file__).parents[4] / "examples" / "study-selection-config.json"
    assert path.exists(), f"selection example not found at {path}"
    return path


@pytest.fixture
def example_qa_config_path():
    path = Path(__file__).parents[4] / "examples" / "study-qa-config.json"
    assert path.exists(), f"QA example not found at {path}"
    return path


@pytest.fixture
def canonical_selection_input(tmp_path, sample_pdf_path, paper_url):
    path = tmp_path / "deduplicated-results.xlsx"
    pd.DataFrame(
        [
            {
                "title": "Linked Data Entity Resolution System",
                "abstract": "A system for resolving linked data entities using configuration learning.",
                "url": paper_url,
                "cluster_id": 1,
                "include": "",
                "exclude_reason": "",
            },
            {
                "title": "A Survey of Entity Matching Methods",
                "abstract": "A review of entity matching methods and existing systems.",
                "url": sample_pdf_path.as_uri(),
                "cluster_id": 2,
                "include": "",
                "exclude_reason": "",
            },
        ]
    ).to_excel(path, index=False)
    return path


@pytest.fixture
def canonical_qa_input(tmp_path, sample_pdf_path, paper_url):
    path = tmp_path / "selected-results.xlsx"
    pd.DataFrame(
        [
            {
                "title": "Linked Data Entity Resolution System",
                "abstract": "A system for resolving linked data entities using configuration learning.",
                "url": paper_url,
                "include": "include",
                "re2": None,
                "ri1": None,
                "r1": None,
            }
        ]
    ).to_excel(path, index=False)
    return path


@pytest.fixture
def provider_factory():
    def make_provider(answers):
        provider = MagicMock()
        provider.ensure_model.return_value = True
        generator = MagicMock()
        generator.generate_json.side_effect = list(answers)
        provider.new_json_generator.return_value = generator
        return MagicMock(return_value=provider)

    return make_provider


@pytest.fixture
def http_responses():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        yield mock


@pytest.fixture
def superficial_reader():
    reader = MagicMock()

    def read_file(path):
        assert Path(path).read_bytes().startswith(b"%PDF")
        return "sample paper text"

    reader.read_file.side_effect = read_file
    return reader
