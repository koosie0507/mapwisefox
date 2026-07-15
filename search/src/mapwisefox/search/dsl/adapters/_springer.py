from typing import Any

import arrow

from ..parser import (
    ValueExpr,
    BinaryExpr,
    UnaryExpr,
    MatchExpr,
    OutputSpecExpr,
    BoolOp,
    MatchType,
)

from ._base import DSLAdapter
from ..parser._ir import DateExpr, Query
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
        self._regex_parts: list[str] = []  # accumulated by emit_match(regex)

    def emit_value(self, node: ValueExpr) -> str:
        if self._handle_unsearchable_fields(node):
            return ""

        val = node.value
        fields = node.fields or self.field_ctx
        for f in fields:
            val = self._VALUE_MAP.get(f, {}).get(val, val)
        if fields:
            return self._apply_fields(f'"{val}"', fields)
        return f'"{val}"'

    def emit_date(self, node: DateExpr) -> Any:
        lo = arrow.get(node.date_lo) if node.date_lo else None
        if lo and lo == lo.floor(frame="year"):
            lo = lo.floor(frame="year").date().isoformat()
        hi = arrow.get(node.date_hi) if node.date_hi else None
        if hi and hi == hi.floor(frame="year"):
            hi = hi.ceil(frame="year").date().isoformat()
        if lo and hi:
            return f'datefrom:"{lo}" AND dateto:"{hi}"'
        elif lo:
            return f'datefrom:"{lo}"'
        elif hi:
            return f'dateto:"{hi}"'
        else:
            return ""

    def emit_binary(self, node: BinaryExpr) -> str:
        if self._handle_unsearchable_fields(node):
            return ""

        left = self.adapt(node.left)
        right = self.adapt(node.right)

        if not left and not right:
            # all child nodes were either unsearchable or in the premium API
            return ""

        if left == right:
            return left or ""

        if left and right and self._is_negation_of(left, right):
            if node.op == BoolOp.AND:
                return ""  # contradiction: a and NOT a -> suppress
            if node.op == BoolOp.OR:
                return left  # tautology: a or NOT a

        op = "AND" if node.op == BoolOp.AND else "OR"
        if not left:
            inner = right
        elif not right:
            inner = left
        else:
            inner = f"{left} {op} {right}"

        if node.fields:
            return self._apply_fields(inner, node.fields)

        return inner

    def emit_not(self, node: UnaryExpr) -> str:
        if self._handle_unsearchable_fields(node):
            return ""

        return self._format_negation(self.adapt(node.child))

    def emit_approx(self, node: MatchExpr) -> str:
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
            return f'"{left_val}" NEAR/{n} "{right_val}"'
        return self.adapt(child)

    def emit_match(self, node: MatchExpr) -> str:
        # node.op == ("match", MatchType)
        match_type = node.op[1]
        inner = self.adapt(node.child)
        if match_type == MatchType.REGEX:
            # Springer API has no regex support.
            # Store the raw pattern for client-side post-retrieval filtering,
            raw = self._raw_value(node.child)
            if raw:
                self._regex_parts.append(raw)
            return inner
        if match_type == MatchType.STRICT:
            if not inner.startswith('"'):
                inner = f'"{inner}"'
            return inner
        return f"{inner}~"

    def emit_output(self, node: OutputSpecExpr) -> str:
        # Springer has no separate filter endpoint; every constraint goes into
        # the same q= string, so we ignore the query/filter distinction here.
        return self.adapt(node.child)

    def emit_query(self, ast_root: Query) -> QueryObject:
        """Top-level method to generate the final Scopus string."""
        result = self._normalize(self.adapt(ast_root.body))
        uq_regex_parts = dict.fromkeys(self._regex_parts)
        result.regex = "|".join(uq_regex_parts) if uq_regex_parts else ""

        return result

    @classmethod
    def _is_unsearchable(cls, field: str) -> bool:
        return field in cls._UNSEARCHABLE_FIELDS

    def _apply_fields(self, expr: str, fields: list[str]) -> str:
        """
        Emit field:expr pairs, OR-joined for disjunctive fields.
        Mirrors SpringerAdapter.ATTR_MAP usage in _emit_factored.
        """
        parts = []
        for f in fields:
            springer_field = self._FIELD_MAP.get(f, f)
            # Skip premium-only fields unless is_premium
            if f in self._PREMIUM_FIELDS and not self._is_premium:
                continue
            parts.append(f"{springer_field}:{expr}")
        if not parts:
            return ""
        return " OR ".join(parts)

    @staticmethod
    def _raw_value(node) -> str:
        """Extract the unquoted string from a ValueExpr, or '' otherwise."""
        if isinstance(node, ValueExpr):
            return node.value
        return ""
