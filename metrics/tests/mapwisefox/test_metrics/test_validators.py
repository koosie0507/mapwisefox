from pathlib import Path

import click
import pytest

from mapwisefox.metrics._validators import (
    validate_input_file_type,
    validate_output_file_type,
)


class FakeParam:
    def __init__(self, name):
        self.name = name


def test_validate_input_file_type_accepts_csv(tmp_path):
    ctx = click.Context(click.Command("x"))
    path = tmp_path / "a.csv"
    path.write_text("id,score\n1,1\n")

    result = validate_input_file_type(ctx, FakeParam("input_file"), str(path))
    assert result == Path(path).resolve()


def test_validate_input_file_type_accepts_list(tmp_path):
    ctx = click.Context(click.Command("x"))
    p1 = tmp_path / "a.csv"
    p2 = tmp_path / "b.xlsx"
    p1.write_text("id,score\n1,1\n")
    pd = pytest.importorskip("pandas")
    pd.DataFrame({"id": [1]}).to_excel(p2, index=False)

    result = validate_input_file_type(ctx, FakeParam("input_file"), [str(p1), str(p2)])
    assert result == [Path(p1).resolve(), Path(p2).resolve()]


def test_validate_input_file_type_rejects_bib(tmp_path):
    ctx = click.Context(click.Command("x"))
    path = tmp_path / "a.bib"
    path.write_text("@article{x, title={x}}\n")

    with pytest.raises(click.BadParameter):
        validate_input_file_type(ctx, FakeParam("input_file"), str(path))


def test_validate_input_file_type_rejects_unknown_value_type():
    ctx = click.Context(click.Command("x"))

    with pytest.raises(click.BadParameter):
        validate_input_file_type(ctx, FakeParam("input_file"), 123)


def test_validate_output_file_type_accepts_xlsx(tmp_path):
    ctx = click.Context(click.Command("x"))
    path = tmp_path / "out.xlsx"

    result = validate_output_file_type(ctx, FakeParam("output_file"), str(path))
    assert result == Path(path).resolve()


def test_validate_output_file_type_returns_none_for_none():
    ctx = click.Context(click.Command("x"))

    assert validate_output_file_type(ctx, FakeParam("output_file"), None) is None
