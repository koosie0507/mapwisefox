from pathlib import Path

import pandas as pd
import pytest
import responses
import openpyxl
import shutil
from unittest.mock import MagicMock

from mapwisefox.assistant.config import AssistantParams
from mapwisefox.assistant.quality_assessment._study_qa import study_qa


@pytest.fixture(autouse=True)
def cleanup_downloads_dir():
    yield
    downloads_dir = Path.cwd() / "downloads"
    shutil.rmtree(downloads_dir, ignore_errors=True)


@pytest.mark.parametrize("reader_type", ["custom", "docling"])
def test_canonical_qa_accepts_http_pdf_for_each_reader(
    runner,
    canonical_qa_input,
    example_qa_config_path,
    sample_pdf_path,
    paper_url,
    http_responses,
    provider_factory,
    superficial_reader,
    monkeypatch,
    reader_type,
):
    http_responses.add(
        responses.GET,
        paper_url,
        body=sample_pdf_path.read_bytes(),
        content_type="application/pdf",
    )
    provider = provider_factory(
        [
            {"score": 8, "reason": "the objectives and method are clearly reported"},
            {"score": 7, "reason": "the evaluation provides relevant evidence"},
            {"score": 9, "reason": "the system is directly relevant"},
        ]
    )
    reader_factory = MagicMock(return_value=superficial_reader)
    monkeypatch.setattr(
        "mapwisefox.assistant.quality_assessment._study_qa.reader_factory",
        reader_factory,
    )
    result = runner.invoke(
        study_qa,
        [
            str(canonical_qa_input),
            "--config",
            str(example_qa_config_path),
            "--reader-type",
            reader_type,
        ],
        obj=AssistantParams(provider_factory=provider, model_choice="gpt_oss"),
    )

    assert result.exit_code == 0, result.output
    output = pd.read_excel(canonical_qa_input.parent / "selected-results-gpt_oss.xlsx")
    assert output.loc[0, "re2"] == 8
    assert output.loc[0, "ri1"] == 7
    assert output.loc[0, "r1"] == 9
    assert "# reporting" in output.loc[0, "evaluation"]
    assert len(http_responses.calls) == 1
    reader_factory.assert_called_once_with(
        reader_type, "lp://PubLayNet/tf_efficientdet_d0/config"
    )


@pytest.mark.parametrize("reader_type", ["custom", "docling"])
def test_canonical_qa_accepts_local_file_url_without_http(
    runner,
    canonical_qa_input,
    example_qa_config_path,
    sample_pdf_path,
    provider_factory,
    superficial_reader,
    http_responses,
    monkeypatch,
    reader_type,
):
    local_input = canonical_qa_input
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["title", "abstract", "url", "include", "re2", "ri1", "r1"])
    sheet.append(
        [
            "Linked Data Entity Resolution System",
            "A system for resolving linked data entities using configuration learning.",
            sample_pdf_path.as_uri(),
            "include",
            None,
            None,
            None,
        ]
    )
    workbook.save(local_input)
    provider = provider_factory(
        [
            {"score": 8, "reason": "clear"},
            {"score": 7, "reason": "appropriate"},
            {"score": 9, "reason": "relevant"},
        ]
    )
    reader_factory = MagicMock(return_value=superficial_reader)
    monkeypatch.setattr(
        "mapwisefox.assistant.quality_assessment._study_qa.reader_factory",
        reader_factory,
    )

    result = runner.invoke(
        study_qa,
        [
            str(local_input),
            "--config",
            str(example_qa_config_path),
            "--reader-type",
            reader_type,
        ],
        obj=AssistantParams(provider_factory=provider, model_choice="gpt_oss"),
    )

    assert result.exit_code == 0, result.output
    assert (local_input.parent / "selected-results-gpt_oss.xlsx").exists()
    assert len(http_responses.calls) == 0
    reader_factory.assert_called_once_with(
        reader_type, "lp://PubLayNet/tf_efficientdet_d0/config"
    )


def test_canonical_qa_handles_http_failure_without_unmocked_network(
    runner,
    canonical_qa_input,
    example_qa_config_path,
    paper_url,
    http_responses,
    provider_factory,
    superficial_reader,
    monkeypatch,
):
    http_responses.add(responses.GET, paper_url, status=503)
    provider = provider_factory([])
    monkeypatch.setattr(
        "mapwisefox.assistant.quality_assessment._study_qa.reader_factory",
        MagicMock(return_value=superficial_reader),
    )

    result = runner.invoke(
        study_qa,
        [str(canonical_qa_input), "--config", str(example_qa_config_path)],
        obj=AssistantParams(provider_factory=provider, model_choice="gpt_oss"),
    )

    assert result.exit_code == 0, result.output
    assert len(http_responses.calls) == 1
    assert (canonical_qa_input.parent / "selected-results-gpt_oss.xlsx").exists()
