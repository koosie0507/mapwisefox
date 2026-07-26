import pytest
from pydantic import ValidationError

from mapwisefox.common.config import (
    QAConfig,
    SelectionConfig,
    SelectionCriterion,
    SelectionResponse,
)


def _criterion(label: str, description: str = "d") -> SelectionCriterion:
    return SelectionCriterion(label=label, description=description)


def test_selection_config_accepts_valid_payload():
    config = SelectionConfig(
        review_topic="find good papers",
        inclusion_criteria=[_criterion("english", "written in English")],
        exclusion_criteria=[_criterion("not primary", "not a primary study")],
    )

    assert config.review_topic == "find good papers"
    assert config.inclusion_criteria[0].label == "english"


def test_selection_config_defaults_additional_context_to_none():
    config = SelectionConfig(
        review_topic="find good papers",
        inclusion_criteria=[_criterion("english")],
        exclusion_criteria=[_criterion("not primary")],
    )

    assert config.additional_context is None


def test_selection_config_accepts_additional_context():
    config = SelectionConfig(
        review_topic="find good papers",
        additional_context="Focus on empirical software studies.",
        inclusion_criteria=[_criterion("english")],
        exclusion_criteria=[_criterion("not primary")],
    )

    assert config.additional_context == "Focus on empirical software studies."


@pytest.mark.parametrize(
    "missing_field", ["review_topic", "inclusion_criteria", "exclusion_criteria"]
)
def test_selection_config_rejects_missing_required_field(missing_field):
    payload = {
        "review_topic": "find good papers",
        "inclusion_criteria": [{"label": "english", "description": "d"}],
        "exclusion_criteria": [{"label": "not primary", "description": "d"}],
    }
    del payload[missing_field]

    with pytest.raises(ValidationError):
        SelectionConfig(**payload)


@pytest.mark.parametrize("empty_field", ["inclusion_criteria", "exclusion_criteria"])
def test_selection_config_rejects_empty_criteria_list(empty_field):
    payload = {
        "review_topic": "find good papers",
        "inclusion_criteria": [{"label": "english", "description": "d"}],
        "exclusion_criteria": [{"label": "not primary", "description": "d"}],
        empty_field: [],
    }

    with pytest.raises(ValidationError):
        SelectionConfig(**payload)


@pytest.mark.parametrize("field", ["inclusion_criteria", "exclusion_criteria"])
def test_selection_config_rejects_duplicate_criterion_labels(field):
    duplicate = {"label": "dup", "description": "d"}
    payload = {
        "review_topic": "find good papers",
        "inclusion_criteria": [duplicate, {"label": "other", "description": "d"}],
        "exclusion_criteria": [duplicate, {"label": "other", "description": "d"}],
        field: [duplicate, duplicate],
    }

    with pytest.raises(ValidationError):
        SelectionConfig(**payload)


def test_selection_criterion_requires_label_and_description():
    with pytest.raises(ValidationError):
        SelectionCriterion(label="only")


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


def test_selection_response_accepts_include_without_justification():
    response = SelectionResponse(answer="include")

    assert response.answer == "include"
    assert response.justification is None


def test_selection_response_accepts_exclude_with_justification():
    response = SelectionResponse(answer="exclude", justification="not relevant")

    assert response.answer == "exclude"
    assert response.justification == "not relevant"


def test_selection_response_rejects_unknown_answer():
    with pytest.raises(ValidationError):
        SelectionResponse(answer="maybe")


def test_selection_response_rejects_non_string_answer():
    with pytest.raises(ValidationError):
        SelectionResponse(answer=123)
