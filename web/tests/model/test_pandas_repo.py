import pytest

from mapwisefox.web.model import PandasRepo


@pytest.fixture
def excel_path(datadir, request):
    if hasattr(request, "param"):
        return datadir / request.param
    return datadir / "pandas_repo_valid_input.xlsx"


@pytest.fixture
def sheet_name(request):
    return request.param if hasattr(request, "param") else "Sheet1"


@pytest.fixture
def pandas_repo(excel_path, sheet_name):
    return PandasRepo(excel_path)


def test_init_pandas_repo(pandas_repo, sheet_name):
    assert pandas_repo is not None