from pathlib import Path
from unittest.mock import MagicMock

from mapwisefox.assistant.judge._study_qa import _evaluate_paper

QA_CONFIG = {"topic": "entity resolution"}
QA_CRITERIA = [
    {
        "label": "re1",
        "category": "reporting",
        "question": "Is it formal?",
        "description": "assess tone",
        "scoring": "1 to 10",
    }
]


def test_evaluate_paper_returns_score_on_first_successful_generation():
    generate_json = MagicMock(return_value={"score": 8, "reason": "good"})

    result = _evaluate_paper(
        "paper text", Path("paper.pdf"), generate_json, QA_CONFIG, QA_CRITERIA
    )

    assert result["re1"]["score"] == 8


def test_evaluate_paper_retries_until_a_truthy_score_is_returned():
    generate_json = MagicMock(
        side_effect=[{"score": None, "reason": "n/a"}, {"score": 8, "reason": "good"}]
    )

    result = _evaluate_paper(
        "paper text", Path("paper.pdf"), generate_json, QA_CONFIG, QA_CRITERIA
    )

    assert result["re1"]["score"] == 8


def test_evaluate_paper_stops_retrying_after_max_score_retries():
    generate_json = MagicMock(return_value={"score": None, "reason": "n/a"})

    _evaluate_paper(
        "paper text",
        Path("paper.pdf"),
        generate_json,
        QA_CONFIG,
        QA_CRITERIA,
        max_score_retries=2,
    )

    assert generate_json.call_count == 3


def test_evaluate_paper_leaves_score_empty_after_max_retries_exceeded():
    generate_json = MagicMock(return_value={"score": None, "reason": "n/a"})

    result = _evaluate_paper(
        "paper text",
        Path("paper.pdf"),
        generate_json,
        QA_CONFIG,
        QA_CRITERIA,
        max_score_retries=2,
    )

    assert result["re1"]["score"] is None


def test_evaluate_paper_records_a_reason_when_left_unscored():
    generate_json = MagicMock(return_value={"score": None, "reason": "n/a"})

    result = _evaluate_paper(
        "paper text",
        Path("paper.pdf"),
        generate_json,
        QA_CONFIG,
        QA_CRITERIA,
        max_score_retries=2,
    )

    assert result["re1"]["reason"]
