from pathlib import Path
import runpy

import pandas as pd
from unittest.mock import Mock

from mapwisefox.snowballing import run_command
from mapwisefox.snowballing.__cli import _normalize_doi, _relations

from .conftest import Paper


def read_output(path, sheet_name):
    return pd.read_excel(path, sheet_name=sheet_name, index_col=0, na_filter=False)


def test_backward_is_default_and_client_closes(runner, workbook, adapter):
    papers, calls, clients = adapter
    papers.update(
        {
            "10/a": Paper("DOI:10/a", references=["DOI:10/b"]),
            "10/b": Paper("DOI:10/b"),
        }
    )
    source = workbook([{"doi": "10/a"}])

    result = runner.invoke(run_command, [str(source)])

    assert result.exit_code == 0, result.output
    assert calls == [["10/a"], ["10/b"]]
    assert clients[0].closed
    assert (
        read_output(source.with_name("papers-snowball.xlsx"), "Back").index.name
        == "cluster_id"
    )


def test_max_depth_aggregates_direct_linked_ids(runner, workbook, adapter):
    papers, _, _ = adapter
    papers.update(
        {
            "10/a": Paper("DOI:10/a", references=["DOI:10/b", "DOI:10/c"]),
            "10/b": Paper("DOI:10/b", references=["DOI:10/c", "DOI:10/d"]),
            "10/c": Paper("DOI:10/c", references=["DOI:10/d"]),
            "10/d": Paper("DOI:10/d"),
        }
    )
    source = workbook([{"doi": "10/a"}])

    result = runner.invoke(run_command, [str(source), "--max-depth", "2"])

    assert result.exit_code == 0, result.output
    output = read_output(source.with_name("papers-snowball.xlsx"), "Back")
    assert output["doi"].tolist() == ["10/b", "10/c", "10/d"]
    assert output.set_index("doi")["referencing_paper_ids"].to_dict() == {
        "10/b": "10/a",
        "10/c": "10/a;10/b",
        "10/d": "10/b;10/c",
    }


def test_forward_uses_custom_linked_ids_column(runner, workbook, adapter):
    papers, _, _ = adapter
    papers.update(
        {
            "10/a": Paper("DOI:10/a", citations=["DOI:10/b"]),
            "10/b": Paper("DOI:10/b", citations=["DOI:10/c"]),
            "10/c": Paper("DOI:10/c"),
        }
    )
    source = workbook([{"doi": "10/a"}])

    result = runner.invoke(
        run_command,
        [
            str(source),
            "--direction",
            "forward",
            "--max-depth",
            "2",
            "--linked-ids-column",
            "linked",
        ],
    )

    assert result.exit_code == 0, result.output
    output = read_output(source.with_name("papers-snowball.xlsx"), "Forward")
    assert output.set_index("doi")["linked"].to_dict() == {
        "10/b": "10/a",
        "10/c": "10/b",
    }


def test_ids_are_normalized_and_exclusions_are_not_expanded(runner, workbook, adapter):
    papers, calls, _ = adapter
    papers["10/a"] = Paper("DOI:10/a", references=["DOI:10/a", "DOI:10/b", "DOI:10/c"])
    papers["10/c"] = Paper("DOI:10/c")
    source = workbook(
        [{"paper_id": " HTTPS://DOI.ORG/10/A "}, {"paper_id": None}],
        sheets={"Excluded": [{"paper_id": "doi:10/B"}]},
    )

    result = runner.invoke(
        run_command,
        [
            str(source),
            "--id-column-name",
            "paper_id",
            "--exclude",
            "Excluded",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [["10/a"], ["10/c"]]
    output = read_output(source.with_name("papers-snowball.xlsx"), "Back")
    assert output["doi"].tolist() == ["10/c"]


def test_paper_in_both_relations_is_not_dropped(runner, workbook, adapter):
    papers, _, _ = adapter
    papers.update(
        {
            "10/a": Paper("DOI:10/a", citations=["DOI:10/b"], references=["DOI:10/b"]),
            "10/b": Paper("DOI:10/b"),
        }
    )
    source = workbook([{"doi": "10/a"}])

    result = runner.invoke(run_command, [str(source)])

    assert result.exit_code == 0, result.output
    assert read_output(source.with_name("papers-snowball.xlsx"), "Back")[
        "doi"
    ].tolist() == ["10/b"]


def test_empty_output_keeps_schema(runner, workbook, adapter):
    papers, _, _ = adapter
    papers["10/a"] = Paper("DOI:10/a")
    source = workbook([{"doi": "10/a"}])

    result = runner.invoke(run_command, [str(source)])

    assert result.exit_code == 0, result.output
    output = read_output(source.with_name("papers-snowball.xlsx"), "Back")
    assert list(output.columns) == [
        "doi",
        "title",
        "authors",
        "abstract",
        "source",
        "url",
        "year",
        "has_pdf",
        "pdf_url",
        "referencing_paper_ids",
        "include",
    ]


def test_in_place_preserves_existing_sheets(runner, workbook, adapter):
    papers, _, _ = adapter
    papers.update(
        {
            "10/a": Paper("DOI:10/a", citations=["DOI:10/b"]),
            "10/b": Paper("DOI:10/b"),
        }
    )
    source = workbook([{"doi": "10/a"}], sheets={"Excluded": [{"doi": "10/z"}]})

    result = runner.invoke(
        run_command, [str(source), "--direction", "forward", "--in-place"]
    )

    assert result.exit_code == 0, result.output
    assert set(pd.ExcelFile(source).sheet_names) == {"Papers", "Excluded", "Forward"}


def test_invalid_column_is_reported_as_cli_error(runner, workbook, adapter):
    source = workbook([{"doi": "10/a"}])

    result = runner.invoke(run_command, [str(source), "--id-column-name", "missing"])

    assert result.exit_code != 0
    assert "missing" in result.output


def test_invalid_max_depth_is_rejected(runner, workbook):
    source = workbook([{"doi": "10/a"}])

    result = runner.invoke(run_command, [str(source), "--max-depth", "0"])

    assert result.exit_code == 2
    assert "0 is not in the range" in result.output


def test_help_describes_command_options(runner):
    result = runner.invoke(run_command, ["--help"])

    assert result.exit_code == 0
    assert "Perform DOI-based citation snowballing" in result.output
    assert "Worksheet containing DOIs to exclude" in result.output
    assert "Maximum number of citation levels" in result.output
    assert "Output column for directly linked paper DOIs" in result.output


def test_missing_input_ids_emit_warning(runner, workbook, adapter):
    papers, _, _ = adapter
    papers["10/a"] = Paper("DOI:10/a")
    source = workbook([{"doi": "10/a"}, {"doi": "10/missing"}])

    result = runner.invoke(run_command, [str(source)])

    assert result.exit_code == 0, result.output
    assert "1 input IDs were not found" in result.output


def test_output_prefix_is_resolved_next_to_input(runner, workbook, adapter):
    papers, _, _ = adapter
    papers["10/a"] = Paper("DOI:10/a")
    source = workbook([{"doi": "10/a"}])

    result = runner.invoke(run_command, [str(source), "--output-prefix", "result"])

    assert result.exit_code == 0, result.output
    assert Path(source.parent / "result-snowball.xlsx").exists()


def test_missing_sheet_is_reported_as_cli_error(runner, workbook, adapter):
    source = workbook([{"doi": "10/a"}])

    result = runner.invoke(run_command, [str(source), "--sheet-name", "Missing"])

    assert result.exit_code != 0
    assert "Missing" in result.output


def test_linked_ids_column_cannot_replace_output_data(runner, workbook, adapter):
    source = workbook([{"doi": "10/a"}])

    result = runner.invoke(run_command, [str(source), "--linked-ids-column", "doi"])

    assert result.exit_code != 0
    assert "conflicts" in result.output


def test_client_closes_when_api_fails(runner, workbook, adapter, monkeypatch):
    from mapwisefox.snowballing import __cli

    _, _, clients = adapter

    class FailingAdapter:
        async def get_many(self, identifiers):
            raise RuntimeError("API failed")

    monkeypatch.setattr(
        __cli, "SemanticScholarAdapter", lambda client: FailingAdapter()
    )
    source = workbook([{"doi": "10/a"}])

    result = runner.invoke(run_command, [str(source)])

    assert result.exit_code != 0
    assert clients[0].closed


def test_invalid_relation_dois_are_ignored():
    paper = Paper("DOI:10/a", references=[None, ""])

    relations = _relations([paper], "backward")

    assert relations == {}


def test_papers_without_dois_are_ignored():
    paper = Paper("", references=["DOI:10/b"])

    relations = _relations([paper], "backward")

    assert relations == {}


def test_normalize_doi_rejects_missing_values():
    assert _normalize_doi(None) is None


def test_module_entrypoint_invokes_command(monkeypatch):
    invocation = Mock()
    monkeypatch.setattr(type(run_command), "__call__", invocation)

    runpy.run_module("mapwisefox.snowballing.__main__", run_name="__main__")

    invocation.assert_called_once()
