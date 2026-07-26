from pathlib import Path

from mapwisefox.assistant.tools import load_template


TEMPLATE_PATH = (
    Path(__file__).parents[4]
    / "src"
    / "mapwisefox"
    / "assistant"
    / "quality_assessment"
    / "_study_qa.j2"
)


def test_qa_template_renders_criterion_context():
    rendered = load_template(TEMPLATE_PATH).render(
        topic="entity resolution",
        question="Is the method clear?",
        description="Assess the reported method.",
        scoring="1 to 10",
    )

    assert "entity resolution" in rendered
    assert "Assess the reported method." in rendered
    assert "1 to 10" in rendered
