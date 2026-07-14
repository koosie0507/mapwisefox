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
    UnaryExpr,
    MatchExpr,
    OutputSpecExpr,
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
    "affil": "AFFIL",
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

    def _map_value(cls, fields, value):
        for f in fields:
            field_value_map = cls._VALUE_MAP.get(f)
            if field_value_map is None:
                continue
            return field_value_map.get(value, value)
        return value

    def emit_value(self, node: ValueExpr) -> str:
        quoted = f'"{self._map_value(node.fields or self.field_ctx, node.value)}"'
        prefix = self._scopus_field_prefix(node.fields)
        return f"{prefix}({quoted})" if prefix else quoted

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

        return {OutputTarget.QUERY: expr, OutputTarget.FILTER: None}

    def emit_binary(self, node: BinaryExpr) -> dict:
        left = self._normalize(self.adapt(node.left))
        right = self._normalize(self.adapt(node.right))

        op = "AND" if node.op == BoolOp.AND else "OR"

        # Merge Queries using the AST operator
        q_left, q_right = left.get(OutputTarget.QUERY), right.get(OutputTarget.QUERY)
        if q_left and q_right:
            query_str = f"{q_left} {op} {q_right}"
        else:
            query_str = q_left or q_right

        # Merge Filters ALWAYS using AND
        f_left, f_right = left.get(OutputTarget.FILTER), right.get(OutputTarget.FILTER)
        if f_left and f_right:
            filter_str = f"{f_left} AND {f_right}"
        else:
            filter_str = f_left or f_right

        # Apply SCOPUS field prefixes if necessary
        if node.fields:
            prefix = self._scopus_field_prefix(node.fields)
            if prefix:
                if query_str:
                    query_str = f"{prefix}({query_str})"
                if filter_str:
                    filter_str = f"{prefix}({filter_str})"

        return {OutputTarget.QUERY: query_str, OutputTarget.FILTER: filter_str}

    def emit_not(self, node: UnaryExpr) -> str:
        return f"NOT {self.adapt(node.child)}"

    def emit_approx(self, node: MatchExpr) -> str:
        # Scopus has no generic approx operator; treat as a grouped expression.
        return f"({self.adapt(node.child)})"

    def emit_nearest(self, node: MatchExpr) -> str:
        # Scopus proximity: term1 W/N term2
        # node.op == ("nearest", N)
        n = node.op[1]
        child = node.child
        if isinstance(child, BinaryExpr):
            left = self.adapt(child.left)
            right = self.adapt(child.right)
            return f"{left} W/{n} {right}"
        return self.adapt(child)

    def emit_match(self, node: MatchExpr) -> str:
        # node.op == ("match", MatchType)
        match_type = node.op[1]
        if match_type == MatchType.REGEX:
            raise NotImplementedError(
                "Scopus does not support regex matching natively. "
                "Use '-> filter:' to apply regex post-retrieval."
            )
        inner = self.adapt(node.child)
        if match_type == MatchType.STRICT:
            # Ensure the value is quoted for an exact-phrase search
            if not inner.startswith('"'):
                inner = f'"{inner}"'
        # MatchType.LOOSE: default Scopus behaviour — no change needed
        return inner

    def _is_fully_enclosed(self, text: str) -> bool:
        """
        Checks if a string is safely enclosed by a single pair of parentheses.
        Prevents redundant grouping like '((A OR B))' while protecting '(A) OR (B)'.
        """
        if not text or not text.startswith("(") or not text.endswith(")"):
            return False

        depth = 0
        for i, char in enumerate(text):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1

            # If depth drops to 0 before the end, it's not a single enclosing group
            # e.g., "(A) AND (B)" drops to 0 after the first ')'
            if depth == 0 and i < len(text) - 1:
                return False

        return depth == 0

    def emit_group(self, node: GroupExpr) -> dict:
        inner = self._normalize(self.adapt(node.child))
        inner_q = inner.get(OutputTarget.QUERY)
        inner_f = inner.get(OutputTarget.FILTER)

        prefix = self._scopus_field_prefix(node.fields) if node.fields else ""

        def safe_wrap(text: str) -> str:
            if not text:
                return None
            # If we have a field prefix, we MUST wrap to bind it: PREFIX(text)
            if prefix:
                return f"{prefix}({text})"
            # If it's already safely enclosed without a prefix, don't double-wrap
            if self._is_fully_enclosed(text):
                return text
            # Otherwise, wrap it to preserve precedence
            return f"({text})"

        result = {}
        if inner_q:
            result[OutputTarget.QUERY] = safe_wrap(inner_q)
        if inner_f:
            result[OutputTarget.FILTER] = safe_wrap(inner_f)

        return result

    def emit_output(self, node: OutputSpecExpr) -> dict:
        child = self._normalize(self.adapt(node.child))

        if node.target == OutputTarget.FILTER:
            # Move whatever the child evaluated to into the filter stream
            content = child[OutputTarget.QUERY] or child[OutputTarget.FILTER]
            return {OutputTarget.QUERY: None, OutputTarget.FILTER: content}

        return {
            OutputTarget.QUERY: child[OutputTarget.QUERY],
            OutputTarget.FILTER: None,
        }

    def emit_query(self, ast_root: Query) -> QueryObject:
        """Top-level method to generate the final Scopus string."""
        result = self._normalize(self.adapt(ast_root.body))
        q = result.get(OutputTarget.QUERY)
        f = result.get(OutputTarget.FILTER)

        content = ""
        if q and f:
            content = f"({q}) AND ({f})"
        elif q:
            content = q
        elif f:
            content = f
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
