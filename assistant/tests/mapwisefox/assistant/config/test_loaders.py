import json

import pytest

from mapwisefox.assistant.config import (
    ConfigValidationError,
    QAConfig,
    SelectionConfig,
    load_qa_config,
    load_selection_config,
)


@pytest.fixture
def qa_config_payload():
    return {
        "topic": "entity resolution",
        "criteria": [
            {
                "label": "re1",
                "category": "reporting",
                "question": "Is it formal?",
                "description": "assess tone",
                "scoring": "1 to 10",
            }
        ],
    }


def _write_json(path, payload):
    path.write_text(json.dumps(payload))
    return path


def test_load_selection_config_returns_model(tmp_path, study_selection_config):
    path = _write_json(tmp_path / "selection.json", study_selection_config)

    config = load_selection_config(path)

    assert isinstance(config, SelectionConfig)


def test_load_selection_config_raises_friendly_error_on_invalid_payload(tmp_path):
    path = _write_json(tmp_path / "selection.json", {"review_topic": "x"})

    with pytest.raises(ConfigValidationError):
        load_selection_config(path)


def test_load_qa_config_returns_model(tmp_path, qa_config_payload):
    path = _write_json(tmp_path / "qa.json", qa_config_payload)

    config = load_qa_config(path)

    assert isinstance(config, QAConfig)


def test_load_qa_config_raises_friendly_error_on_invalid_payload(tmp_path):
    path = _write_json(tmp_path / "qa.json", {"topic": "x", "criteria": []})

    with pytest.raises(ConfigValidationError):
        load_qa_config(path)
