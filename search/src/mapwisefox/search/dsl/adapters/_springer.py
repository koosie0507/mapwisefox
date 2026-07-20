import arrow

from ..parser import (
    ValueExpr,
    BoolOp,
)

from ._base import DSLAdapter
from ..parser._ir import DateExpr, NearExpr, Query
from ...query import QueryObject


class SpringerDSLAdapter(DSLAdapter):
    _FIELD_MAP: dict[str, str] = {
        "title": "title",
        "abstract": "abstract",
        "keywords": "keyword",
        "author": "name",
        "language": "language",
        "subject": "discipline",
        "evidence_type": "type",
    }
    _VALUE_MAP: dict[str, dict[str, object]] = {
        "evidence_type": {
            "article": "Journal",
            "conference": "Journal",
        }
    }
    _UNSEARCHABLE_FIELDS: set[str] = {"title", "abstract"}
    _PREMIUM_FIELDS = {
        "subject",
        "discipline",
        "language",
        "articletype",
        "pub",
        "year",
        "license",
        "dateloaded",
        "dateloadedfrom",
        "dateloadedto",
        "country",
        "topicalcollection",
        "journalonlinefirst:true",
        "issuetype",
        "issue",
        "volume",
        "ContainsElements",
        "Exclude:Bibliography",
        "grid",
        "orcid",
        "bookdoi",
        "latest issue",
        "earliest issue",
        "openaccess:true",
        "free:true",
    }

    def __init__(self, is_premium: bool = False):
        super().__init__()
        self._is_premium = is_premium

    def emit_value(self, node: ValueExpr) -> QueryObject:
        val = node.value
        fields = self._get_all_node_fields(node)
        for f in fields:
            val = self._VALUE_MAP.get(f, {}).get(val, val)
        val = f'"{val.strip('"')}"'
        q_obj = self._emit_leaf_targets(fields, val)
        if fields:
            q_obj = self._apply_fields(q_obj, fields)
        return q_obj

    def emit_near(self, node: NearExpr) -> QueryObject:
        """Translate ``near[n](a, b)`` to the native ``NEAR/n`` operator."""
        fields = self._get_all_node_fields(node)
        term = f'"{node.left.value}" NEAR/{node.distance} "{node.right.value}"'
        q_obj = self._emit_leaf_targets(fields, term)
        if fields:
            q_obj = self._apply_fields(q_obj, fields)
        return q_obj

    def emit_date(self, node: DateExpr) -> QueryObject:
        lo = arrow.get(node.date_lo) if node.date_lo else None
        if lo and lo == lo.floor(frame="year"):
            lo = lo.floor(frame="year").date().isoformat()
        hi = arrow.get(node.date_hi) if node.date_hi else None
        if hi and hi == hi.floor(frame="year"):
            hi = hi.ceil(frame="year").date().isoformat()

        filters = {}
        if lo:
            filters["datefrom"] = [f'"{lo}"']
        if hi:
            filters["dateto"] = [f'"{hi}"']

        return QueryObject(filters=filters)

    def emit_query(self, ast_root: Query) -> QueryObject:
        result = self._normalize(self.adapt(ast_root.body))
        filter_clauses = [
            self._enclose_field(attr, filter_clause) if attr else filter_clause
            for attr, filters in result.filters.items()
            for filter_clause in filters
        ]
        compound_filter_clause = self._format_filter_clauses(filter_clauses)
        content = ""
        if result.query and result.filters:
            content = f"{result.query} {self._map_bool_op(BoolOp.AND)} {compound_filter_clause}"
        elif result.query:
            content = result.query
        elif result.filters:
            content = compound_filter_clause
        return QueryObject(query=content, regex=result.regex)

    def _is_regex_field(self, field: str) -> bool:
        return field in self._UNSEARCHABLE_FIELDS

    def _enclose_field(self, field: str, query: str) -> str:
        return f"{field}:{query}"

    def _is_field_supported(self, field: str) -> bool:
        result = super()._is_field_supported(field)
        if not self._is_premium:
            result &= field not in self._PREMIUM_FIELDS
        return result

    @classmethod
    def _map_field_name(cls, field: str) -> str:
        return cls._FIELD_MAP.get(field, field)

    @classmethod
    def _format_filter_clauses(cls, operands: list) -> str:
        operand_str = f" {cls._map_bool_op(BoolOp.AND)} ".join(operands)
        if len(operands) > 1:
            operand_str = f"({operand_str})"
        return operand_str
