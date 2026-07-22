import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from click.testing import CliRunner

from mapwisefox.assistant.config import AssistantParams
from mapwisefox.assistant.judge._study_qa import study_qa


@pytest.fixture
def runner():
    return CliRunner()


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
