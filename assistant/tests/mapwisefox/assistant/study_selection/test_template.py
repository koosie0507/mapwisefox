from pathlib import Path

from mapwisefox.assistant.config import SelectionConfig
from mapwisefox.assistant.tools import load_template


TEMPLATE_PATH = (
    Path(__file__).parents[4]
    / "src"
    / "mapwisefox"
    / "assistant"
    / "study_selection"
    / "_study_selection.j2"
)


def test_selection_template_renders_without_additional_context():
    config = SelectionConfig(
        review_topic="entity resolution",
        inclusion_criteria=["written in English"],
        exclusion_criteria=["not a primary study"],
    )

    rendered = load_template(TEMPLATE_PATH).render(**config.model_dump())

    assert "entity resolution" in rendered
    assert "written in English" in rendered
    assert "not a primary study" in rendered


def test_selection_template_renders_additional_context():
    config = SelectionConfig(
        review_topic="entity resolution",
        additional_context="Prioritize architecture descriptions.",
        inclusion_criteria=["written in English"],
        exclusion_criteria=["not a primary study"],
    )

    rendered = load_template(TEMPLATE_PATH).render(**config.model_dump())

    assert "Prioritize architecture descriptions." in rendered
