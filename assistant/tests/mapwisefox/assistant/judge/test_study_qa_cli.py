import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from mapwisefox.assistant.config import AssistantParams
from mapwisefox.assistant.judge._study_qa import study_qa
from mapwisefox.assistant.tools.pdf import (
    ExtractionFailureReason,
    FileContentsExtractionError,
)


@pytest.fixture
def input_file(tmp_path):
    path = tmp_path / "papers.xlsx"
    pd.DataFrame([{"url": "file:///tmp/paper.pdf"}]).to_excel(path, index=False)
    return path


@pytest.fixture
def invalid_qa_config_path(tmp_path):
    path = tmp_path / "qa.json"
    path.write_text(json.dumps({"topic": "entity resolution", "criteria": []}))
    return path


@pytest.fixture
def valid_qa_config_path(tmp_path):
    path = tmp_path / "qa.json"
    path.write_text(
        json.dumps(
            {
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
        )
    )
    return path


def _obj_that_stops_after_ensure_model():
    provider = MagicMock()
    provider.ensure_model.return_value = False
    return AssistantParams(
        provider_factory=MagicMock(return_value=provider), model_choice="gpt_oss"
    )


@patch("mapwisefox.assistant.judge._study_qa.reader_factory")
@patch("mapwisefox.assistant.judge._study_qa.load_df")
@patch("mapwisefox.assistant.judge._study_qa.FileProvider")
def test_study_qa_verifies_tls_by_default(
    mock_file_provider,
    mock_load_df,
    mock_reader_factory,
    runner,
    input_file,
    valid_qa_config_path,
):
    mock_load_df.return_value = pd.DataFrame(
        [{"url": "file:///tmp/paper.pdf", "re1": None}]
    )

    runner.invoke(
        study_qa,
        [str(input_file), "--config", str(valid_qa_config_path)],
        obj=_obj_that_stops_after_ensure_model(),
    )

    assert mock_file_provider.call_args.kwargs["verify_tls"] is True


@patch("mapwisefox.assistant.judge._study_qa.reader_factory")
@patch("mapwisefox.assistant.judge._study_qa.load_df")
@patch("mapwisefox.assistant.judge._study_qa.FileProvider")
def test_study_qa_can_disable_tls_verification(
    mock_file_provider,
    mock_load_df,
    mock_reader_factory,
    runner,
    input_file,
    valid_qa_config_path,
):
    mock_load_df.return_value = pd.DataFrame(
        [{"url": "file:///tmp/paper.pdf", "re1": None}]
    )

    runner.invoke(
        study_qa,
        [
            str(input_file),
            "--config",
            str(valid_qa_config_path),
            "--insecure-skip-tls-verify",
        ],
        obj=_obj_that_stops_after_ensure_model(),
    )

    assert mock_file_provider.call_args.kwargs["verify_tls"] is False


def test_study_qa_reports_error_for_invalid_config_without_touching_provider(
    runner, input_file, invalid_qa_config_path
):
    obj = AssistantParams(provider_factory=None, model_choice="gpt_oss")

    result = runner.invoke(
        study_qa,
        [str(input_file), "--config", str(invalid_qa_config_path)],
        obj=obj,
    )

    assert result.exit_code != 0


def test_study_qa_public_command_writes_scores_and_evaluation(
    runner, input_file, valid_qa_config_path, tmp_path, monkeypatch
):
    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"pdf")
    data = pd.DataFrame([{"url": "file:///paper.pdf", "re1": None}])
    provider = MagicMock()
    provider.ensure_model.return_value = True
    provider.new_json_generator.return_value.generate_json.return_value = {
        "score": 8,
        "reason": "clearly reported",
    }
    reader = MagicMock()
    reader.read_file.return_value = "paper text"
    provider_factory = MagicMock(return_value=provider)

    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.load_df", MagicMock(return_value=data)
    )
    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.FileProvider",
        MagicMock(return_value=MagicMock(return_value=paper)),
    )
    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.reader_factory",
        MagicMock(return_value=reader),
    )

    result = runner.invoke(
        study_qa,
        [str(input_file), "--config", str(valid_qa_config_path)],
        obj=AssistantParams(provider_factory=provider_factory, model_choice="gpt_oss"),
    )

    assert result.exit_code == 0, result.output
    output = pd.read_excel(input_file.parent / "papers-gpt_oss.xlsx")
    assert output.loc[0, "re1"] == 8
    assert "clearly reported" in output.loc[0, "evaluation"]


def test_study_qa_public_command_leaves_unscored_criterion_empty(
    runner, input_file, valid_qa_config_path, tmp_path, monkeypatch
):
    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"pdf")
    data = pd.DataFrame([{"url": "file:///paper.pdf", "re1": None}])
    provider = MagicMock()
    provider.ensure_model.return_value = True
    provider.new_json_generator.return_value.generate_json.return_value = {
        "score": None,
        "reason": "no score",
    }
    reader = MagicMock()
    reader.read_file.return_value = "paper text"

    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.load_df", MagicMock(return_value=data)
    )
    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.FileProvider",
        MagicMock(return_value=MagicMock(return_value=paper)),
    )
    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.reader_factory",
        MagicMock(return_value=reader),
    )

    result = runner.invoke(
        study_qa,
        [str(input_file), "--config", str(valid_qa_config_path)],
        obj=AssistantParams(
            provider_factory=MagicMock(return_value=provider), model_choice="gpt_oss"
        ),
    )

    assert result.exit_code == 0, result.output
    output = pd.read_excel(input_file.parent / "papers-gpt_oss.xlsx")
    assert pd.isna(output.loc[0, "re1"])
    assert "left unscored" in output.loc[0, "evaluation"]


def test_study_qa_public_command_uses_failsafe_reader_after_reader_failure(
    runner, input_file, valid_qa_config_path, tmp_path, monkeypatch
):
    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"pdf")
    data = pd.DataFrame([{"url": "file:///paper.pdf", "re1": None}])
    failing_reader = MagicMock()
    failing_reader.read_file.side_effect = FileContentsExtractionError(
        ExtractionFailureReason.BackendError, paper
    )
    fallback_reader = MagicMock()
    fallback_reader.read_file.return_value = "paper text"
    provider = MagicMock()
    provider.ensure_model.return_value = True
    provider.new_json_generator.return_value.generate_json.return_value = {
        "score": 7,
        "reason": "adequate",
    }

    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.load_df", MagicMock(return_value=data)
    )
    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.FileProvider",
        MagicMock(return_value=MagicMock(return_value=paper)),
    )
    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.reader_factory",
        MagicMock(return_value=failing_reader),
    )
    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.get_default_pdf_reader",
        MagicMock(return_value=fallback_reader),
    )

    result = runner.invoke(
        study_qa,
        [str(input_file), "--config", str(valid_qa_config_path)],
        obj=AssistantParams(
            provider_factory=MagicMock(return_value=provider), model_choice="gpt_oss"
        ),
    )

    assert result.exit_code == 0, result.output
    assert fallback_reader.read_file.called


def test_study_qa_public_command_records_download_failure(
    runner, input_file, valid_qa_config_path, monkeypatch
):
    data = pd.DataFrame([{"url": "https://example.com/paper.pdf", "re1": None}])
    provider = MagicMock()
    provider.ensure_model.return_value = True

    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.load_df", MagicMock(return_value=data)
    )
    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.FileProvider",
        MagicMock(return_value=MagicMock(side_effect=ValueError("bad download"))),
    )
    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.reader_factory", MagicMock()
    )

    result = runner.invoke(
        study_qa,
        [str(input_file), "--config", str(valid_qa_config_path)],
        obj=AssistantParams(
            provider_factory=MagicMock(return_value=provider), model_choice="gpt_oss"
        ),
    )

    assert result.exit_code == 0, result.output


def test_study_qa_public_command_skips_evaluation_failure(
    runner, input_file, valid_qa_config_path, tmp_path, monkeypatch
):
    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"pdf")
    data = pd.DataFrame([{"url": "file:///paper.pdf", "re1": None}])
    reader = MagicMock()
    reader.read_file.return_value = "paper text"
    provider = MagicMock()
    provider.ensure_model.return_value = True
    provider.new_json_generator.return_value.generate_json.side_effect = RuntimeError(
        "LLM failure"
    )

    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.load_df", MagicMock(return_value=data)
    )
    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.FileProvider",
        MagicMock(return_value=MagicMock(return_value=paper)),
    )
    monkeypatch.setattr(
        "mapwisefox.assistant.judge._study_qa.reader_factory",
        MagicMock(return_value=reader),
    )

    result = runner.invoke(
        study_qa,
        [str(input_file), "--config", str(valid_qa_config_path)],
        obj=AssistantParams(
            provider_factory=MagicMock(return_value=provider), model_choice="gpt_oss"
        ),
    )

    assert result.exit_code == 0, result.output
