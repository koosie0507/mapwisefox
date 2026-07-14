import pytest

from mapwisefox.search.dsl.parser import Parser


@pytest.fixture(scope="module")
def parse():
    return Parser()
