import json
import pytest


@pytest.fixture
def study_selection_config():
    return {
        "review_topic": "find good papers",
        "inclusion_criteria": ["written in English"],
        "exclusion_criteria": ["not a primary study"],
    }


@pytest.fixture
def valid_selection_config_path(tmp_path, study_selection_config):
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(study_selection_config))
    return path
