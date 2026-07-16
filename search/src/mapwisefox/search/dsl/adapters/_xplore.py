from typing import Any

import arrow
from mapwisefox.search.query import QueryObject

from ._base import DSLAdapter
from ..parser import DateExpr, ValueExpr, BoolOp


class XploreDSLAdapter(DSLAdapter):
    _FIELD_MAP = {
        "title": "Document Title",
        "abstract": "Abstract",
        "author": "Authors",
        "keywords": "Author Keywords",
        "affiliation": "Author Affiliations",
        "evidence_type": "content_type",
    }
    _VALUE_MAP = {
        "evidence_type": {
            "article": "Journals",
            "conference": "Conferences",
        }
    }
    _ALWAYS_FILTER_FIELDS = {"evidence_type"}

    def emit_value(self, node: ValueExpr) -> Any:
        all_fields = self._get_all_node_fields(node)
        q_obj = self._emit_leaf_targets(all_fields, self._map_value(node))
        if all_fields:
            q_obj = self._apply_fields(q_obj, all_fields)
        return q_obj

    def emit_date(self, node: DateExpr) -> Any:
        result = QueryObject()
        if node.date_lo:
            result.filters["start_year"] = [arrow.get(node.date_lo).format("YYYY")]
        if node.date_hi:
            result.filters["end_year"] = [arrow.get(node.date_hi).format("YYYY")]
        return result

    @classmethod
    def _is_field_supported(cls, field: str) -> bool:
        return field in cls._FIELD_MAP

    def _is_filter_field(self, field: str) -> bool:
        return super()._is_filter_field(field) or field in self._ALWAYS_FILTER_FIELDS

    def _enclose_field(self, field: str, query: str) -> str:
        if all(c not in query for c in ["*", "?"]):
            query = f'"{query}"'
        return f'"{field}":{query}'

    def _map_field_name(cls, field: str) -> str:
        return cls._FIELD_MAP.get(field, field)

    def _map_value(self, node: ValueExpr) -> str:
        all_fields = self._get_all_node_fields(node)
        try:
            return next(
                val
                for val in (
                    val_dict.get(node.value, node.value)
                    for val_dict in (
                        self._VALUE_MAP.get(field, {}) for field in all_fields
                    )
                    if val_dict is not None and node.value in val_dict
                )
            )
        except StopIteration:
            return node.value

    @classmethod
    def _format_filter_clauses(cls, operands: list) -> str:
        operand_str = f" {cls._map_bool_op(BoolOp.AND)} ".join(operands)
        if len(operands) > 1:
            operand_str = f"({operand_str})"
        return operand_str
