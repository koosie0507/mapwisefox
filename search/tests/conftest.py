from os import access, R_OK
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def datadir():
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def load_data_file(datadir):
    def _(filename):
        fpath = datadir / filename
        if not fpath.exists() or not fpath.is_file() or not access(fpath, R_OK):
            raise ValueError("the test_cases fixture requires path to a readable file")
        return fpath.read_text(encoding="utf-8")
    return _


@pytest.fixture
def test_cases(request, load_data_file, datadir):
    if not hasattr(request, "param"):
        raise ValueError("the test_cases fixture must be parametrized")
    return list(map(lambda x: x.strip(), load_data_file(request.param).split("---")))
