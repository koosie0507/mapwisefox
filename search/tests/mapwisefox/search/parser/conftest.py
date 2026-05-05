import pytest

from mapwisefox.search.parser import Parser


@pytest.fixture(scope="module")
def parse():
    return Parser()
