from typing import Any

import arrow

from ._base import DSLAdapter
from ..parser import GroupExpr
from ..parser._ir import BinaryExpr, ValueExpr, DateExpr, Query
from ...query import QueryObject


class AcmDSLAdapter(DSLAdapter):
    _FIELD_MAP = {
        "title": "Title",
        "abstract": "Abstract",
        "keywords": "Keyword",
        "published": "E-Publication Date",
        "evidence_type": "Article Type",
    }
    _VALUE_MAP = {
        "evidence_type": {
            "article": "Research Article",
            "conference": "Research Article",
        }
    }
    _FILTER_FIELDS: set[str] = {"evidence_type", "language", "subject"}

    def emit_value(self, node: ValueExpr) -> Any:
        val = node.value
        fields = self._get_all_node_fields(node)
        for f in fields:
            val = self._VALUE_MAP.get(f, {}).get(val, val)
        val = f'"{val.strip('"')}"'
        expr = self._emit_leaf_targets(fields, val)
        if node.fields:
            expr = self._apply_fields(expr, node.fields)
        return expr

    def emit_date(self, node: DateExpr) -> Any:
        lo = arrow.get(node.date_lo) if node.date_lo else None
        if lo and lo == lo.floor(frame="year"):
            lo = lo.floor(frame="year").format("MM/DD/YYYY")
        hi = arrow.get(node.date_hi) if node.date_hi else None
        if hi and hi == hi.floor(frame="year"):
            hi = hi.ceil(frame="year").format("MM/DD/YYYY")

        field_name = self._FIELD_MAP.get(node.field, node.field)
        filters = {}
        if lo and hi:
            filters[field_name] = [f"({lo} TO {hi})"]
        elif lo:
            filters[field_name] = [f"({lo} TO *)"]
        elif hi:
            filters[field_name] = [f"(* TO {hi})"]

        return QueryObject(filters=filters)

    def emit_binary(self, node: BinaryExpr) -> QueryObject:
        inner = super().emit_binary(node)
        if node.fields:
            inner = self._apply_fields(inner, node.fields)
        return inner

    def emit_group(self, node: GroupExpr) -> QueryObject:
        result = super().emit_group(node)
        if node.fields:
            result = self._apply_fields(result, node.fields)
        return result

    def emit_query(self, ast_root: Query) -> QueryObject:
        """Top-level method to generate the final Scopus string."""
        result = self._normalize(self.adapt(ast_root.body))
        result.filters = {
            k: [v.strip('"') for v in clauses] for k, clauses in result.filters.items()
        }
        return result

    def _enclose_field(self, field: str, query: str) -> str:
        return f"{field}:{query}"

    def _is_filter_field(self, field: str) -> bool:
        if field not in self._FIELD_MAP:
            return False
        return super()._is_filter_field(field) or field in self._FILTER_FIELDS

    def _is_query_field(self, field: str) -> bool:
        return super()._is_query_field(field) and field in self._FIELD_MAP

    @classmethod
    def _map_field_name(cls, field: str) -> str:
        return cls._FIELD_MAP.get(field, field)
