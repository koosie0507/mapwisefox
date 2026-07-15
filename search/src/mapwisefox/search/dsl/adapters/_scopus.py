"""
Scopus DSL adapter.

Mirrors the field-mapping and group-collapsing logic of the original
ScopusAdapter (FlatOutputAdapter) but walks the DSL IR instead of
the QueryBuilder NaryExpr tree.

Scopus Advanced Search syntax reference:
  https://dev.elsevier.com/sc_search_tips.html
"""

from typing import Any

import arrow

from ..parser import (
    ValueExpr,
    BinaryExpr,
    GroupExpr,
    MatchExpr,
    OutputTarget,
    BoolOp,
    MatchType,
    Query,
)
from ._base import DSLAdapter
from ..parser._ir import DateExpr
from ...query import QueryObject

_FIELD_MAP: dict[str, str] = {
    "title": "TITLE",
    "abstract": "ABS",
    "keywords": "AUTHKEY",
    "author": "AUTH",
    "affiliation": "AFFIL",
    "evidence_type": "DOCTYPE",
    "language": "LANGUAGE",
    "subject": "SUBJAREA",
}


_COMBINED: dict[frozenset, str] = {
    frozenset({"title", "abstract"}): "TITLE-ABS",
    frozenset({"title", "abstract", "keywords"}): "TITLE-ABS-KEY",
}


class ScopusDSLAdapter(DSLAdapter):
    """
    Translates DSL IR into a Scopus Advanced Search query string.

    Output routing (OutputSpecExpr):
      -> query   → the main Scopus query string; filter is None
      -> filter  → query is None; string returned as a post-retrieval hint
      -> both    → same string used for both
    """

    _DATE_FIELD_MAP: dict[str, str] = {
        "published": "PUBYEAR",
        # add more DSL date fields here
    }

    _VALUE_MAP: dict[str, dict[str, str | None]] = {
        "evidence_type": {
            "article": "ar",
            "conference": "cp",
            # "book" is intentionally absent → treated as None (dropped)
        },
        "subject": {"computer science": "COMP"},
    }

    @classmethod
    def _map_value(cls, fields, value):
        for f in fields:
            field_value_map = cls._VALUE_MAP.get(f)
            if field_value_map is None:
                continue
            return field_value_map.get(value, value)
        return value

    def emit_value(self, node: ValueExpr) -> QueryObject:
        fields = node.fields or self.field_ctx
        quoted = f'"{self._map_value(fields, node.value)}"'
        prefix = (
            self._scopus_field_prefix(node.fields)
            if self.output_ctx == OutputTarget.QUERY
            else self._scopus_field_prefix(fields)
        )
        return self._emit_leaf_target(prefix, quoted)

    def emit_date(self, node: DateExpr) -> Any:
        scopus_field = self._DATE_FIELD_MAP.get(node.field, node.field.upper())
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

        return self._emit_leaf_target("", expr)

    @staticmethod
    def _merge_filters(left_clauses, right_clauses):
        return list(
            filter(
                lambda x: x is not None and len(x.strip()) > 0,
                dict.fromkeys(left_clauses + right_clauses),
            )
        )

    @staticmethod
    def _format_filter_clauses(operand: list) -> str:
        operand_str = " AND ".join(operand)
        if len(operand) > 1:
            operand_str = f"({operand_str})"
        return operand_str

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

        # Apply SCOPUS field prefixes if necessary
        if node.fields:
            prefix = self._scopus_field_prefix(node.fields)
            if prefix:
                if query_str:
                    query_str = f"{prefix}({query_str})"

        return QueryObject(query=query_str, filters=filters)

    def emit_approx(self, node: MatchExpr) -> str:
        # Scopus has no generic approx operator; treat as a grouped expression.
        return f"({self.adapt(node.child)})"

    def emit_nearest(self, node: MatchExpr) -> str:
        n = int(node.op[1])
        child = node.child
        if isinstance(child, BinaryExpr):
            left = self.adapt(child.left)
            right = self.adapt(child.right)
            return f"{left} W/{n} {right}"
        return self.adapt(child)

    def emit_match(self, node: MatchExpr) -> str:
        match_type = str(node.op[1])
        inner = self.adapt(node.child)
        if match_type == MatchType.STRICT:
            if not inner.startswith('"'):
                inner = f'"{inner}"'
        return inner

    def emit_group(self, node: GroupExpr) -> QueryObject:
        inner = self._normalize(self.adapt(node.child))
        prefix = self._scopus_field_prefix(node.fields) if node.fields else ""

        def safe_wrap(text: str) -> str:
            if not text:
                return ""
            # If we have a field prefix, we MUST wrap to bind it: PREFIX(text)
            if prefix and self.output_ctx == OutputTarget.QUERY:
                return f"{prefix}({text})"
            # If it's already safely enclosed without a prefix, don't double-wrap
            if self._is_fully_enclosed(text):
                return text
            # Otherwise, wrap it to preserve precedence
            return f"({text})"

        filters = (
            self._merge_dicts(
                inner.filters,
                {prefix: [inner.query]},
                self._merge_filters,
            )
            if self.output_ctx == OutputTarget.FILTER
            else inner.filters
        )
        result = QueryObject(query=safe_wrap(inner.query), filters=filters)
        return result

    def emit_query(self, ast_root: Query) -> QueryObject:
        """Top-level method to generate the final Scopus string."""
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

    @staticmethod
    def _scopus_field_prefix(fields: list[str]) -> str:
        """
        Map a list of DSL field names to a Scopus field prefix.
        Mirrors the TITLE-ABS collapsing in the original _extract_group_str.
        """
        if not fields:
            return ""
        key = frozenset(fields)
        if key in _COMBINED:
            return _COMBINED[key]
        if len(fields) == 1:
            return _FIELD_MAP.get(fields[0], fields[0].upper())
        # Multiple unmapped fields — fall back to the broadest combined prefix
        return "TITLE-ABS-KEY"
