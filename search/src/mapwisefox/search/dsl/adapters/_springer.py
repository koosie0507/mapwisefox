import re as _re
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
        if self._redir_unsearchable(node):
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
        if self._redir_unsearchable(node):
            return ""

        op = "AND" if node.op == BoolOp.AND else "OR"
        left = self.adapt(node.left)
        right = self.adapt(node.right)

        def _is_negation_of(a: str, b: str) -> bool:
            return a == self._format_negation(a) or b == self._format_negation(a)

        if left == right:
            return left or ""

        if left and right and _is_negation_of(left, right):
            if node.op == BoolOp.AND:
                return ""  # contradiction: a and NOT a -> suppress
            if node.op == BoolOp.OR:
                return left  # tautology: a or NOT a

        if not left and not right:
            # all child nodes were either unsearchable or in the premium API
            return ""
        if not left:
            inner = right
        elif not right:
            inner = left
        else:
            inner = f"{left} {op} {right}"

        if node.fields:
            return self._apply_fields(inner, node.fields)

        return inner

    @staticmethod
    def _format_negation(val):
        return f"NOT {val}"

    def emit_not(self, node: UnaryExpr) -> str:
        if self._redir_unsearchable(node):
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

    def emit_group(self, node: GroupExpr) -> str:
        if self._redir_unsearchable(node):
            return ""
        inner = self.adapt(node.child)
        if not inner:
            return ""

        return f"({inner})" if self._needs_parentheses(inner) else inner

    def emit_output(self, node: OutputSpecExpr) -> str:
        # Springer has no separate filter endpoint; every constraint goes into
        # the same q= string, so we ignore the query/filter distinction here.
        return self.adapt(node.child)

    def emit_query(self, ast_root: Query) -> QueryObject:
        """Top-level method to generate the final Scopus string."""
        result = self._normalize(self.adapt(ast_root.body))
        q = result.get(OutputTarget.QUERY)
        uq_regex_parts = dict.fromkeys(self._regex_parts)
        regex = "|".join(uq_regex_parts) if uq_regex_parts else ""

        return QueryObject(query=q, filters={}, regex=regex)

    def _redir_unsearchable(self, node) -> bool:
        fields = getattr(node, "fields", [])
        searchable = [f for f in fields if f not in self._UNSEARCHABLE_FIELDS]
        unsearchable = [f for f in fields if f in self._UNSEARCHABLE_FIELDS]

        if len(unsearchable) == 0:
            return False

        pattern = self._create_regex(node)
        if pattern:
            self._regex_parts.append(pattern)
        node.fields = searchable

        return len(searchable) == 0

    @staticmethod
    def _needs_parentheses(s: str) -> bool:
        if not s:
            return False
        if BoolOp.AND not in s and BoolOp.OR not in s:
            return False
        if s.startswith("(") and s.endswith(")"):
            depth = 0
            for i, ch in enumerate(s):
                match ch:
                    case "(":
                        depth += 1
                    case ")":
                        depth -= 1
                if depth == 0 and i < len(s) - 1:
                    # ((...)..) ) - open paren closed before end, needs parentheses
                    break
            else:
                return False  # fully wrapped, no other parentheses needed
        return True

    def _apply_fields(self, expr: str, fields: list[str]) -> str:
        """
        Emit field:expr pairs, OR-joined for disjunctive fields.
        Mirrors SpringerAdapter.ATTR_MAP usage in _emit_factored.
        """
        parts = []
        for f in fields:
            springer_field = self._FIELD_MAP.get(f, f)
            # Skip premium-only fields unless is_premium
            if f in {"language", "subject"} and not self._is_premium:
                continue
            parts.append(f"{springer_field}:{expr}")
        if not parts:
            return ""
        return " OR ".join(parts)

    def _create_regex(self, node) -> str:
        """
        Recursively convert an AST subtree into a client-side regex pattern.

        AND  →  left_pattern .+ right_pattern
        OR   →  (v1|v2|…)  via _flatten_or
        leaf →  _regex_atom(value)
        """
        if isinstance(node, BinaryExpr):
            if node.op == BoolOp.AND:
                left_re = self._create_regex(node.left)
                right_re = self._create_regex(node.right)
                if left_re and right_re:
                    return f"{left_re}.+{right_re}"
                return left_re or right_re
            # OR chain — flatten then wrap in a group
            parts = self._flatten_or(node)
            atoms = [self._regex_atom(v) for v in parts]
            return f"({'|'.join(atoms)})"
        if isinstance(node, ValueExpr):
            return self._regex_atom(node.value)
        if isinstance(node, GroupExpr):
            return self._create_regex(node.child)
        return ""

    def _flatten_or(self, node) -> list[str]:
        """
        Flatten a left-recursive OR chain into a list of raw values.

        Lark's LALR parser builds left-nested trees for `a | b | c | … | g`,
        i.e. OR(OR(...OR(a, b)..., y), z). Visiting right-before-left yields
        values in *reversed* input order, which matches the expected regex
        ordering (most-recently-added term first).
        """
        if isinstance(node, BinaryExpr) and node.op == BoolOp.OR:
            # right-first to produce the expected reversed ordering
            return self._flatten_or(node.right) + self._flatten_or(node.left)
        if isinstance(node, ValueExpr):
            return [node.value]
        if isinstance(node, GroupExpr):
            return self._flatten_or(node.child)
        return []

    @staticmethod
    def _regex_atom(value: str) -> str:
        """
        Convert a DSL value (possibly containing the glob wildcard `*`) to a
        regex atom.  All regex-special characters are escaped first, then the
        escaped wildcard `\\*` is replaced with `.*`.
        """
        return _re.escape(value).replace(r"\*", ".*")

    @staticmethod
    def _raw_value(node) -> str:
        """Extract the unquoted string from a ValueExpr, or '' otherwise."""
        if isinstance(node, ValueExpr):
            return node.value
        return ""
