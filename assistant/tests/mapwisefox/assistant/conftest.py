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
            {
                "label": "published 2010-2025",
                "description": "published between 2010 and 2025",
            },
            {
                "label": "english primary",
                "description": "written in English and is a primary study",
            },
            {
                "label": "er software",
                "description": "the title or abstract refers to a tool, framework, system, library, or software architecture for entity resolution",
            },
        ],
        "exclusion_criteria": [
            {
                "label": "secondary study",
                "description": "is a review, survey, tutorial, position paper, or another secondary study",
            },
            {
                "label": "matching subproblem",
                "description": "the title or abstract focuses only on a matching subproblem such as blocking, clustering, classification, or filtering",
            },
            {
                "label": "domain-specific only",
                "description": "the title or abstract describes only a domain-specific application without referring to a generic entity resolution software artifact",
            },
        ],
    }


@pytest.fixture
def valid_selection_config_path(tmp_path, study_selection_config):
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(study_selection_config))
    return path
