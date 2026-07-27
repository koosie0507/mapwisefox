"""Shared fixtures for Split CLI tests."""

import json
from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """Provide a synchronous Click command runner."""
    return CliRunner()


@pytest.fixture
def workbook(tmp_path: Path):
    """Create an Excel workbook with a default or named worksheet."""

    def create(
        rows: list[dict], *, name: str = "studies.xlsx", sheet: str = "Studies"
    ) -> Path:
        path = tmp_path / name
        pd.DataFrame(rows).to_excel(path, sheet_name=sheet, index=False)
        return path

    return create


@pytest.fixture
def criteria_config(tmp_path: Path) -> Path:
    """Provide a primary study QA-compatible criteria configuration."""
    path = tmp_path / "criteria.json"
    path.write_text(
        json.dumps(
            {
                "criteria": [
                    {"label": "clear_objectives"},
                    {"label": "appropriate_design"},
                ]
            }
        )
    )
    return path
