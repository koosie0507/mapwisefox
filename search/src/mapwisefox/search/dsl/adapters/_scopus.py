from typing import Any

import arrow

from ..parser import (
    ValueExpr,
    BinaryExpr,
    BoolOp,
    Query,
)
from ._base import DSLAdapter
from ..parser._ir import DateExpr, GroupExpr, NearExpr
from ...query import QueryObject


class ScopusDSLAdapter(DSLAdapter):
    _FIELD_MAP: dict[str, str] = {
        "title": "TITLE",
        "abstract": "ABS",
        "keywords": "AUTHKEY",
        "author": "AUTH",
        "affiliation": "AFFIL",
        "evidence_type": "DOCTYPE",
        "language": "LANGUAGE",
        "subject": "SUBJAREA",
        "published": "PUBYEAR",
    }

    _COMBINED: dict[frozenset, str] = {
        frozenset({"title", "abstract"}): "TITLE-ABS",
        frozenset({"title", "abstract", "keywords"}): "TITLE-ABS-KEY",
    }

    _VALUE_MAP: dict[str, dict[str, str | None]] = {
        "evidence_type": {
            "article": "ar",
            "conference": "cp",
            # "book" is intentionally absent → treated as None (dropped)
        },
        "subject": {"computer science": "COMP"},
    }

    def emit_value(self, node: ValueExpr) -> QueryObject:
        fields = self._get_all_node_fields(node)
        quoted = f'"{self._map_value(fields, node.value)}"'
        expr = self._emit_leaf_targets(fields, quoted)
        if node.fields:
            expr = self._apply_fields(expr, node.fields)
        return expr

    def emit_near(self, node: NearExpr) -> QueryObject:
        """Translate ``near[n](a, b)`` to the native ``W/n`` operator."""
        fields = self._get_all_node_fields(node)
        left_val = self._map_value(fields, node.left.value)
        right_val = self._map_value(fields, node.right.value)
        term = f'"{left_val}" W/{node.distance} "{right_val}"'
        expr = self._emit_leaf_targets(fields, term)
        if node.fields:
            expr = self._apply_fields(expr, node.fields)
        return expr

    def emit_date(self, node: DateExpr) -> Any:
        scopus_field = self._FIELD_MAP.get(node.field, node.field.upper())
        start_date = arrow.get(node.date_lo)
        end_date = arrow.get(node.date_hi)

        if node.op == "after":
            expr = f"{scopus_field} AFT '{start_date.isoformat()}'"
        elif node.op == "before":
            expr = f"{scopus_field} BEF '{end_date.isoformat()}"
        elif node.op == "between":
            # Scopus uses strict > / <, so expand the range by 1 year on each side
            sd_repr = start_date.isoformat()
            if start_date.floor(frame="year") == start_date:
                sd_repr = start_date.date().year - 1
            ed_repr = end_date.isoformat()
            if end_date.floor(frame="year") == end_date:
                ed_repr = end_date.date().year + 1
            expr = f"({scopus_field} AFT {sd_repr} AND {scopus_field} BEF {ed_repr})"
        else:
            raise ValueError(f"Unknown date operator: {node.op!r}")
        return QueryObject(query=expr)

    def emit_binary(self, node: BinaryExpr) -> QueryObject:
        left = self._normalize(self.adapt(node.left))
        right = self._normalize(self.adapt(node.right))

        op = "AND" if node.op == BoolOp.AND else "OR"

        if left.query and right.query:
            query_str = f"{left.query} {op} {right.query}"
        else:
            query_str = left.query or right.query

        if left.filters and right.filters:
            filters = self._merge_dicts(
                left.filters,
                right.filters,
                lambda x, y: [
                    f"{self._format_filter_clauses(x)} {op} {self._format_filter_clauses(y)}"
                ],
            )
        else:
            filters = left.filters or right.filters

        q_obj = QueryObject(query=query_str, filters=filters)
        if node.fields:
            q_obj = self._apply_fields(q_obj, node.fields)
        return q_obj

    def emit_group(self, node: GroupExpr) -> QueryObject:
        result = super().emit_group(node)
        if node.fields:
            result = self._apply_fields(result, node.fields)
        return result

    def emit_query(self, ast_root: Query) -> QueryObject:
        result = self._normalize(self.adapt(ast_root.body))
        filter_clauses = [
            f"{attr}({filter_clause})" if attr else filter_clause
            for attr, filters in result.filters.items()
            for filter_clause in filters
        ]
        compound_filter_clause = self._format_filter_clauses(filter_clauses)
        content = ""
        if result.query and result.filters:
            content = f"({result.query}) AND {compound_filter_clause}"
        elif result.query:
            content = result.query
        elif result.filters:
            content = compound_filter_clause
        return QueryObject(query=content)

    def _map_field_names(self, fields: list[str]) -> list[str]:
        """
        Map a list of DSL field names to a Scopus field prefix.
        Mirrors the TITLE-ABS collapsing in the original _extract_group_str.
        """
        if not fields:
            return []
        result = []
        fieldset = set(fields)
        for key, value in self._COMBINED.items():
            if fieldset.issuperset(key):
                result.append(value)
                fieldset.difference_update(key)
        result.extend(
            map(self._map_field_name, filter(lambda f: f in fieldset, fields))
        )
        return result

    def _enclose_field(self, field: str, query: str) -> str:
        if self._is_fully_enclosed(query):
            return f"{field}{query}"
        return f"{field}({query})"

    @classmethod
    def _map_field_name(cls, field: str) -> str:
        return cls._FIELD_MAP.get(field, field)

    @staticmethod
    def _format_filter_clauses(operand: list) -> str:
        operand_str = " AND ".join(operand)
        if len(operand) > 1:
            operand_str = f"({operand_str})"
        return operand_str

    @classmethod
    def _map_value(cls, fields, value):
        for f in fields:
            field_value_map = cls._VALUE_MAP.get(f)
            if field_value_map is None:
                continue
            return field_value_map.get(value, value)
        return value
