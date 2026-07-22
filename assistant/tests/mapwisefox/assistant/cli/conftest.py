import json
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest
import responses


@pytest.fixture
def sample_pdf_path():
    path = Path(__file__).parents[3] / "data" / "sample.pdf"
    assert path.exists(), f"sample PDF not found at {path}"
    return path


@pytest.fixture
def paper_url():
    return "https://papers.example.test/sample.pdf"


@pytest.fixture
def qa_config_path(tmp_path):
    path = tmp_path / "qa-config.json"
    path.write_text(
        json.dumps(
            {
                "topic": "linked data entity resolution systems",
                "criteria": [
                    {
                        "label": "reporting",
                        "category": "reporting",
                        "question": "Are the study objectives and research method clearly reported?",
                        "description": "Assess whether the paper states its objectives and explains the research method sufficiently for a reader to understand what was done.",
                        "scoring": "1 to 10, higher means clearer and more complete reporting",
                    },
                    {
                        "label": "rigour",
                        "category": "rigour",
                        "question": "Is the evaluation appropriate for the stated objectives?",
                        "description": "Assess whether the evaluation design, datasets, baselines, and reported evidence are appropriate for the study objectives.",
                        "scoring": "1 to 10, higher means stronger methodological rigour",
                    },
                    {
                        "label": "relevance",
                        "category": "relevance",
                        "question": "How relevant is the study to software architecture research on entity resolution systems?",
                        "description": "Assess how directly the paper describes a reusable entity resolution system and its architecture rather than only an isolated matching technique.",
                        "scoring": "1 to 10, higher means more directly relevant",
                    },
                ],
            }
        )
    )
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
                "reporting": None,
                "rigour": None,
                "relevance": None,
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
