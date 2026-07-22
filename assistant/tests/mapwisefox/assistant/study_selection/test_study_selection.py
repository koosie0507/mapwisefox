import json
from unittest.mock import MagicMock

import pandas as pd
import pytest

from mapwisefox.assistant.config import AssistantParams, SelectionResponse
from mapwisefox.assistant.study_selection._study_selection import study_selection


@pytest.fixture
def search_results_path(tmp_path):
    path = tmp_path / "results.xlsx"
    pd.DataFrame([{"title": "T1", "abstract": "A1"}]).to_excel(path, index=False)
    return path


def _fake_provider(ensure_model=True, answers=None):
    answers = list(answers or [{"answer": "include"}])
    generator = MagicMock()
    generator.generate_json.side_effect = answers
    provider = MagicMock()
    provider.ensure_model.return_value = ensure_model
    provider.new_json_generator.return_value = generator
    return provider


def _obj(provider_factory):
    return AssistantParams(provider_factory=provider_factory, model_choice="gpt_oss")


def test_study_selection_uses_context_provider_factory(
    runner, valid_selection_config_path, search_results_path
):
    provider = _fake_provider()
    provider_factory = MagicMock(return_value=provider)

    runner.invoke(
        study_selection,
        [str(search_results_path), "--config-file", str(valid_selection_config_path)],
        obj=_obj(provider_factory),
    )

    provider_factory.assert_called_once()


def test_study_selection_exits_nonzero_when_ensure_model_fails(
    runner, valid_selection_config_path, search_results_path
):
    provider_factory = MagicMock(return_value=_fake_provider(ensure_model=False))

    result = runner.invoke(
        study_selection,
        [str(search_results_path), "--config-file", str(valid_selection_config_path)],
        obj=_obj(provider_factory),
    )

    assert result.exit_code != 0


def test_study_selection_does_not_call_new_json_generator_when_ensure_model_fails(
    runner, valid_selection_config_path, search_results_path
):
    provider = _fake_provider(ensure_model=False)
    provider_factory = MagicMock(return_value=provider)

    runner.invoke(
        study_selection,
        [str(search_results_path), "--config-file", str(valid_selection_config_path)],
        obj=_obj(provider_factory),
    )

    provider.new_json_generator.assert_not_called()


def test_study_selection_writes_include_status_to_output(
    runner, valid_selection_config_path, search_results_path
):
    provider_factory = MagicMock(
        return_value=_fake_provider(answers=[{"answer": "include"}])
    )

    result = runner.invoke(
        study_selection,
        [str(search_results_path), "--config-file", str(valid_selection_config_path)],
        obj=_obj(provider_factory),
    )

    assert result.exit_code == 0
    output_path = search_results_path.parent / "results-gpt_oss.xlsx"
    written = pd.read_excel(output_path)
    assert written.loc[0, "include"] == "include"


def test_study_selection_writes_exclude_reason_to_output(
    runner, valid_selection_config_path, search_results_path
):
    provider_factory = MagicMock(
        return_value=_fake_provider(
            answers=[{"answer": "exclude", "justification": "not English"}]
        )
    )

    runner.invoke(
        study_selection,
        [str(search_results_path), "--config-file", str(valid_selection_config_path)],
        obj=_obj(provider_factory),
    )

    output_path = search_results_path.parent / "results-gpt_oss.xlsx"
    written = pd.read_excel(output_path)
    assert written.loc[0, "exclude_reason"] == "not English"


def test_study_selection_passes_response_schema_to_generator(
    runner, valid_selection_config_path, search_results_path
):
    provider = _fake_provider()
    provider_factory = MagicMock(return_value=provider)

    result = runner.invoke(
        study_selection,
        [str(search_results_path), "--config-file", str(valid_selection_config_path)],
        obj=_obj(provider_factory),
    )

    assert result.exit_code == 0, result.output
    call_kwargs = (
        provider.new_json_generator.return_value.generate_json.call_args.kwargs
    )
    assert call_kwargs["response_schema"] == SelectionResponse.model_json_schema()


@pytest.mark.parametrize(
    "invalid_config",
    [
        {"review_topic": "x"},
        {"review_topic": "x", "inclusion_criteria": ["abc"]},
        {"inclusion_criteria": ["abc"], "exclusion_criteria": ["def"]},
        {
            "review_topic": 123,
            "inclusion_criteria": ["abc"],
            "exclusion_criteria": ["def"],
        },
        {
            "review_topic": "x",
            "inclusion_criteria": "abc",
            "exclusion_criteria": ["def"],
        },
        {
            "review_topic": "x",
            "inclusion_criteria": ["abc"],
            "exclusion_criteria": "def",
        },
        {
            "review_topic": "x",
            "additional_context": 123,
            "inclusion_criteria": ["abc"],
            "exclusion_criteria": "def",
        },
    ],
)
def test_study_selection_reports_error_for_invalid_config(
    runner, tmp_path, search_results_path, invalid_config
):
    invalid_config_path = tmp_path / "invalid.json"
    invalid_config_path.write_text(json.dumps(invalid_config))
    provider_factory = MagicMock(return_value=_fake_provider())

    result = runner.invoke(
        study_selection,
        [str(search_results_path), "--config-file", str(invalid_config_path)],
        obj=_obj(provider_factory),
    )

    assert result.exit_code != 0
    provider_factory.assert_not_called()
