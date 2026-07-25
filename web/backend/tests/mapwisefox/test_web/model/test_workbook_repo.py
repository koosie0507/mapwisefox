from copy import copy

import pytest
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill

from mapwisefox.web.model import (
    WorkbookRepository,
    WorkbookValidationError,
    metadata_path,
)


HEADERS = [
    "title",
    "abstract",
    "doi",
    "authors",
    "keywords",
    "year",
    "source",
    "url",
    "has_pdf",
    "referencing_paper_ids",
    "notes",
]
ROW = [
    "A title",
    "An abstract",
    "10.1/example",
    "Ada;Grace",
    "testing;software",
    2024,
    "Journal",
    "https://example.test",
    False,
    "",
    "preserve me",
]


@pytest.fixture
def source_workbook(tmp_path):
    path = tmp_path / "source.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Studies"
    worksheet.append(HEADERS)
    worksheet.append(ROW)
    worksheet.append(["Second", *ROW[1:]])
    worksheet["A2"].fill = PatternFill(fill_type="solid", fgColor="00FF00")
    # add a second sheet that must not be touched
    calculations = workbook.create_sheet("Calculations")
    calculations["A1"] = "=1+1"
    workbook.save(path)
    workbook.close()
    return path


@pytest.fixture
def imported_workbook(tmp_path, source_workbook):
    destination = tmp_path / "screening.xlsx"
    metadata = WorkbookRepository.import_workbook(
        source_workbook,
        destination,
        "Studies",
        ["title", "abstract"],
        "decision",
        "reason",
    )
    return destination, metadata


def test_import_persists_resolved_metadata(imported_workbook):
    destination, metadata = imported_workbook

    persisted = WorkbookRepository.read_metadata(destination)

    assert persisted == metadata


def test_import_appends_missing_screening_columns(imported_workbook):
    destination, _ = imported_workbook

    workbook = load_workbook(destination)
    headers = [cell.value for cell in workbook["Studies"][1]]
    workbook.close()

    assert headers[-2:] == ["decision", "reason"]


def test_import_rejects_missing_expected_column(source_workbook, tmp_path):
    with pytest.raises(WorkbookValidationError, match="missing") as error:
        WorkbookRepository.import_workbook(
            source_workbook,
            tmp_path / "output.xlsx",
            "Studies",
            ["missing"],
            "decision",
            "reason",
        )

    assert error.value.code == "missing_expected_columns"


def test_import_rejects_internal_blank_row(source_workbook, tmp_path):
    workbook = load_workbook(source_workbook)
    worksheet = workbook["Studies"]
    worksheet.insert_rows(3)
    workbook.save(source_workbook)
    workbook.close()

    with pytest.raises(WorkbookValidationError) as error:
        WorkbookRepository.import_workbook(
            source_workbook,
            tmp_path / "output.xlsx",
            "Studies",
            ["title"],
            "decision",
            "reason",
        )

    assert error.value.code == "blank_record_row"


def test_update_preserves_unrelated_workbook_content(imported_workbook):
    destination, metadata = imported_workbook
    before = load_workbook(destination)
    original_fill = copy(before["Studies"]["A2"].fill)
    before.close()

    WorkbookRepository(destination, metadata).update(0, "excluded", ["not software"])

    after = load_workbook(destination, data_only=False)
    assert after["Studies"]["K2"].value == "preserve me"
    assert after["Studies"]["A2"].fill == original_fill
    assert after["Calculations"]["A1"].value == "=1+1"
    after.close()


def test_update_changes_only_screening_values(imported_workbook):
    destination, metadata = imported_workbook

    record = WorkbookRepository(destination, metadata).update(
        0, "excluded", ["not software", "not english"]
    )

    assert record.decision == "excluded"
    assert record.exclusion_reasons == ["not software", "not english"]


def test_delete_removes_workbook_metadata(imported_workbook):
    destination, metadata = imported_workbook

    WorkbookRepository(destination, metadata).delete()

    assert not destination.exists()
    assert not metadata_path(destination).exists()
