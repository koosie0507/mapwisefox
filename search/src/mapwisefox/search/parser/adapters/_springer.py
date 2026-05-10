"""
Springer DSL adapter.

Mirrors the factored-query + regex logic of the original SpringerAdapter
(ExprTreeAdapter) but walks the DSL IR instead of the QueryBuilder NaryExpr
tree.

Springer Meta API query syntax:
  https://dev.springernature.com/adding-constraints

Lucene-like syntax:
  field:"value" AND field:"value"
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
    "title": "title",
    "abstract": "Abstract",
    "keywords": "keyword",
    "author": "name",
    "language": "language",  # premium only
    "subject": "subject",  # premium only
    "doctype": "type",
}

# Fields that Springer supports as disjunctive (OR'd) field prefixes
_DISJUNCTIVE_FIELDS = {"title", "abstract"}


class SpringerDSLAdapter(DSLAdapter):
    """
    Translates DSL IR into a Springer Meta API query dict.

    Returns:
      {"query": str | None, "filter": str | None, "regex": str | None}

    The "regex" key carries a client-side pattern to apply to retrieved
    titles/abstracts, mirroring SpringerAdapter._build_regex.

    Output routing (OutputSpecExpr):
      -> query   → query string sent to the API; no post-filter
      -> filter  → query is None; string used as a post-retrieval filter
      -> both    → same string for both
    """

    def __init__(self, is_premium: bool = False):
        self._is_premium = is_premium
        self._regex_parts: list[str] = []  # accumulated by emit_match(regex)

    # ── abstract implementations ──────────────────────────────────────────────

    def emit_value(self, node: ValueExpr) -> str:
        val = node.value
        if node.fields:
            return self._apply_fields(f'"{val}"', node.fields)
        return f'"{val}"'

    def emit_binary(self, node: BinaryExpr) -> str:
        op = "AND" if node.op == BoolOp.AND else "OR"
        left = self.adapt(node.left)
        right = self.adapt(node.right)
        inner = f"({left} {op} {right})"
        if node.fields:
            return self._apply_fields(inner, node.fields)
        return inner

    def emit_not(self, node: UnaryExpr) -> str:
        # Lucene / Springer: NOT <expr>
        return f"NOT {self.adapt(node.child)}"

    # ── match variants ────────────────────────────────────────────────────────

    def emit_approx(self, node: MatchExpr) -> str:
        # Lucene fuzzy: strip quotes and append ~
        # Works best on single-term values
        inner = self.adapt(node.child).strip('"')
        return f'"{inner}"~'

    def emit_nearest(self, node: MatchExpr) -> str:
        # Lucene phrase proximity: "term1 term2"~N
        # node.op == ("nearest", N)
        n = node.op[1]
        child = node.child
        if isinstance(child, BinaryExpr):
            left_val = self._raw_value(child.left)
            right_val = self._raw_value(child.right)
            return f'"{left_val} {right_val}"~{n}'
        return self.adapt(child)

    def emit_match(self, node: MatchExpr) -> str:
        # node.op == ("match", MatchType)
        match_type = node.op[1]
        inner = self.adapt(node.child)
        if match_type == MatchType.REGEX:
            # Springer API has no regex support.
            # Store the raw pattern for client-side post-retrieval filtering,
            # mirroring SpringerAdapter._build_regex, and emit a broad query.
            raw = self._raw_value(node.child)
            if raw:
                self._regex_parts.append(raw)
            return inner  # broad query; regex applied client-side
        if match_type == MatchType.STRICT:
            # Exact phrase — ensure the value is quoted
            if not inner.startswith('"'):
                inner = f'"{inner}"'
            return inner
        # MatchType.LOOSE — Lucene fuzzy suffix
        return f"{inner}~"

    # ── group ─────────────────────────────────────────────────────────────────

    def emit_group(self, node: GroupExpr) -> str:
        inner = self.adapt(node.child)
        if node.fields:
            return self._apply_fields(f"({inner})", node.fields)
        return f"({inner})"

    # ── output routing ────────────────────────────────────────────────────────

    def emit_output(self, node: OutputSpecExpr) -> dict:
        child_str = self.adapt(node.child)
        regex = "|".join(self._regex_parts) if self._regex_parts else None
        if node.target == OutputTarget.FILTER:
            return {"query": None, "filter": child_str, "regex": regex}
        if node.target == OutputTarget.BOTH:
            return {"query": child_str, "filter": child_str, "regex": regex}
        return {"query": child_str, "filter": None, "regex": regex}

    # ── helpers ───────────────────────────────────────────────────────────────

    def _apply_fields(self, expr: str, fields: list[str]) -> str:
        """
        Emit field:expr pairs, OR-joined for disjunctive fields.
        Mirrors SpringerAdapter.ATTR_MAP usage in _emit_factored.
        """
        parts = []
        for f in fields:
            springer_field = _FIELD_MAP.get(f, f)
            # Skip premium-only fields unless is_premium
            if f in {"language", "subject"} and not self._is_premium:
                continue
            parts.append(f"{springer_field}:{expr}")
        if not parts:
            return expr  # no valid field mapping — emit bare value
        return " OR ".join(parts)

    @staticmethod
    def _raw_value(node) -> str:
        """Extract the unquoted string from a ValueExpr, or '' otherwise."""
        if isinstance(node, ValueExpr):
            return node.value
        return ""
