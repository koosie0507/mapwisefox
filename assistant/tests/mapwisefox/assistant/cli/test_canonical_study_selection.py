import pandas as pd

from mapwisefox.assistant.config import AssistantParams
from mapwisefox.assistant.study_selection._study_selection import study_selection


def test_canonical_deduplicated_results_are_selected(
    runner, canonical_selection_input, valid_selection_config_path, provider_factory
):
    provider = provider_factory(
        [
            {"answer": "include"},
            {"answer": "exclude", "justification": "a secondary study"},
        ]
    )
    result = runner.invoke(
        study_selection,
        [
            str(canonical_selection_input),
            "--config-file",
            str(valid_selection_config_path),
        ],
        obj=AssistantParams(provider_factory=provider, model_choice="gpt_oss"),
    )

    assert result.exit_code == 0, result.output
    output = pd.read_excel(
        canonical_selection_input.parent / "deduplicated-results-gpt_oss.xlsx"
    )
    assert output["include"].tolist() == ["include", "exclude"]
    assert output.loc[1, "exclude_reason"] == "a secondary study"
