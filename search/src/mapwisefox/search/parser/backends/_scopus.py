"""
Scopus DSL adapter.

Mirrors the field-mapping and group-collapsing logic of the original
ScopusAdapter (FlatOutputAdapter) but walks the DSL IR instead of
the QueryBuilder NaryExpr tree.

Scopus Advanced Search syntax reference:
  https://dev.elsevier.com/sc_search_tips.html
"""

from .._base import DSLAdapter
from .._ir import (
    ValueExpr,
    BinaryExpr,
    GroupExpr,
    UnaryExpr,
    MatchExpr,
    OutputSpecExpr,
    OutputTarget,
    BoolOp,
    MatchType,
)

# ── field mapping ─────────────────────────────────────────────────────────────

_FIELD_MAP: dict[str, str] = {
    "title": "TITLE",
    "abstract": "ABS",
    "keywords": "KEY",
    "author": "AUTH",
    "affil": "AFFIL",
}

# Multi-field shortcuts — mirrors _extract_group_str's TITLE-ABS logic
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

    # ── abstract implementations ──────────────────────────────────────────────

    def emit_value(self, node: ValueExpr) -> str:
        quoted = f'"{node.value}"'
        prefix = self._scopus_field_prefix(node.fields)
        return f"{prefix}({quoted})" if prefix else quoted

    def emit_binary(self, node: BinaryExpr) -> str:
        op = "AND" if node.op == BoolOp.AND else "OR"
        left = self.adapt(node.left)
        right = self.adapt(node.right)
        inner = f"{left} {op} {right}"
        if node.fields:
            prefix = self._scopus_field_prefix(node.fields)
            return f"{prefix}({inner})" if prefix else f"({inner})"
        return inner

    def emit_not(self, node: UnaryExpr) -> str:
        # Scopus: AND NOT <expr>  (caller is responsible for the leading AND)
        return f"AND NOT {self.adapt(node.child)}"

    # ── match variants ────────────────────────────────────────────────────────

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

    # ── group ─────────────────────────────────────────────────────────────────

    def emit_group(self, node: GroupExpr) -> str:
        inner = self.adapt(node.child)
        if node.fields:
            prefix = self._scopus_field_prefix(node.fields)
            return f"{prefix}({inner})" if prefix else f"({inner})"
        return f"({inner})"

    # ── output routing ────────────────────────────────────────────────────────

    def emit_output(self, node: OutputSpecExpr) -> dict:
        child_str = self.adapt(node.child)
        if node.target == OutputTarget.FILTER:
            return {"query": None, "filter": child_str}
        if node.target == OutputTarget.BOTH:
            return {"query": child_str, "filter": child_str}
        return {"query": child_str, "filter": None}

    # ── helpers ───────────────────────────────────────────────────────────────

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
