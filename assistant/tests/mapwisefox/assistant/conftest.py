import json

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def study_selection_config():
    return {
        "review_topic": "software architecture of entity resolution systems",
        "additional_context": "Focus on reusable software systems, frameworks, or tools rather than isolated matching algorithms.",
        "inclusion_criteria": [
            "published between 2010 and 2025",
            "written in English",
            "is a primary study",
            "describes a software system, framework, or tool for entity resolution",
            "provides information about the system or software architecture",
        ],
        "exclusion_criteria": [
            "is a review or another secondary study",
            "focuses only on matching, blocking, clustering, or filtering without describing a reusable system",
            "describes only a domain-specific application without a generic entity resolution solution",
        ],
    }


@pytest.fixture
def valid_selection_config_path(tmp_path, study_selection_config):
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(study_selection_config))
    return path
