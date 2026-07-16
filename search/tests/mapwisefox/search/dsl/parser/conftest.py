import pytest

from mapwisefox.search.dsl.parser import Parser, DateExpr, ValueExpr
from mapwisefox.search.dsl.adapters import DSLAdapter


class StubAdapter(DSLAdapter):
    def _enclose_field(self, field: str, query: str) -> str:
        return f"{field}:{query}"

    def __init__(self, re_fields=None):
        super().__init__()
        self._re_fields = re_fields or []

    def _is_regex_field(self, field) -> bool:
        return field in self._re_fields

    def emit_date(self, node: DateExpr) -> str:
        return f"{node.field}({node.date_lo},{node.date_hi},{node.op})"

    def emit_value(self, node: ValueExpr) -> str:
        fields = self._get_all_node_fields(node)
        fields = f" in {fields}" if fields else ""
        return f"VAL({node.value}{fields})"


@pytest.fixture(scope="module")
def parse():
    return Parser()


@pytest.fixture(scope="module")
def stub_adapter(request):
    if hasattr(request, "param"):
        return StubAdapter(*request.param)
    return StubAdapter()
