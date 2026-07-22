import pytest
from pydantic import ValidationError

from mapwisefox.assistant.config import QAConfig, SelectionConfig


def test_selection_config_accepts_valid_payload():
    config = SelectionConfig(
        review_topic="find good papers",
        inclusion_criteria=["written in English"],
        exclusion_criteria=["not a primary study"],
    )

    assert config.review_topic == "find good papers"


@pytest.mark.parametrize(
    "missing_field", ["study_objective", "inclusion_criteria", "exclusion_criteria"]
)
def test_selection_config_rejects_missing_required_field(missing_field):
    payload = {
        "study_objective": "find good papers",
        "inclusion_criteria": ["written in English"],
        "exclusion_criteria": ["not a primary study"],
    }
    del payload[missing_field]

    with pytest.raises(ValidationError):
        SelectionConfig(**payload)


@pytest.mark.parametrize("empty_field", ["inclusion_criteria", "exclusion_criteria"])
def test_selection_config_rejects_empty_criteria_list(empty_field):
    payload = {
        "study_objective": "find good papers",
        "inclusion_criteria": ["written in English"],
        "exclusion_criteria": ["not a primary study"],
        empty_field: [],
    }

    with pytest.raises(ValidationError):
        SelectionConfig(**payload)


def test_qa_config_accepts_valid_payload():
    config = QAConfig(
        topic="entity resolution",
        criteria=[
            {
                "label": "re1",
                "category": "reporting",
                "question": "Is it formal?",
                "description": "assess tone",
                "scoring": "1 to 10",
            }
        ],
    )

    assert config.criteria[0].label == "re1"


def test_qa_config_rejects_empty_criteria_list():
    with pytest.raises(ValidationError):
        QAConfig(topic="entity resolution", criteria=[])


def test_qa_config_rejects_duplicate_criterion_labels():
    criterion = {
        "label": "re1",
        "category": "reporting",
        "question": "Is it formal?",
        "description": "assess tone",
        "scoring": "1 to 10",
    }

    with pytest.raises(ValidationError):
        QAConfig(topic="entity resolution", criteria=[criterion, criterion])
