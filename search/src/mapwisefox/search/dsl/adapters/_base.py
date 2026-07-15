import re as _re
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from functools import singledispatchmethod
from typing import Any, Callable

from ..parser._ir import (
    Query,
    BoolOp,
    ValueExpr,
    BinaryExpr,
    UnaryExpr,
    MatchExpr,
    GroupExpr,
    OutputSpecExpr,
    OutputTarget,
    DateExpr,
)
from ...query import QueryObject


class DSLAdapter(metaclass=ABCMeta):
    _REGEX_NORM_KEY = "regex"

    def __init__(self):
        self._field_ctx_stack: list[list[str]] = []
        self._output_ctx_stack: list[OutputTarget] = []
        self._regex_parts: list[str] = []

    @classmethod
    def _normalize(cls, value: str | dict | QueryObject | None) -> QueryObject | None:
        """Ensure all nodes consistently return a ``QueryObject``.

        If ``value`` is a ``str`` then only the ``query`` attribute of the
        ``QueryObject`` is initialized. If it's a ``dict``, we look for specific
        ``OutputTarget`` keys in the dict, plus the special ``regex`` key.
        ``None`` input values simply pass through, as do ``QueryObject`` values.

        :param value: input value that must be converted to a ``QueryObject``

        :return: a ``QueryObject`` initialized per type specific rules applied
            to the input ``value``.
        :raises: ``ValueError`` is raised if the input value type is not
            supported.
        """
        if value is None:
            return None

        match value:
            case str():
                return QueryObject(query=value)
            case dict():
                return QueryObject(
                    query=value.get(OutputTarget.QUERY, ""),
                    filters=value.get(OutputTarget.FILTER, {}),
                    regex=value.get(cls._REGEX_NORM_KEY, {}),
                )
            case QueryObject():
                return value
            case _:
                raise ValueError(
                    "normalization is supported for instances of type str, dict and QueryObject"
                )

    @property
    def field_ctx(self) -> list[str]:
        """Get the innermost active field context pushed by the closest enclosing GroupExpr."""
        return self._field_ctx_stack[-1] if self._field_ctx_stack else []

    @property
    def output_ctx(self) -> OutputTarget:
        """Get the current active output target."""
        return (
            self._output_ctx_stack[-1] if self._output_ctx_stack else OutputTarget.QUERY
        )

    @contextmanager
    def _scoped_fields(self, fields: list[str]):
        if fields:
            self._field_ctx_stack.append(fields)
        try:
            yield
        finally:
            if fields:
                self._field_ctx_stack.pop()

    @contextmanager
    def _scoped_output(self, output: OutputTarget):
        self._output_ctx_stack.append(output)
        try:
            yield
        finally:
            self._output_ctx_stack.pop()

    @singledispatchmethod
    def adapt(self, node: Any) -> Any:
        raise TypeError(f"No adapter registered for IR node type: {type(node)!r}")

    @adapt.register(Query)
    def _(self, node: Query) -> Any:
        return self.emit_query(node)

    @adapt.register(ValueExpr)
    def _(self, node: ValueExpr) -> Any:
        return self.emit_value(node)

    @adapt.register(DateExpr)
    def _(self, node: DateExpr) -> Any:
        return self.emit_date(node)

    @adapt.register(BinaryExpr)
    def _(self, node: BinaryExpr) -> Any:
        return self.emit_binary(node)

    @adapt.register(UnaryExpr)
    def _(self, node: UnaryExpr) -> Any:
        return self.emit_not(node)

    @adapt.register(MatchExpr)
    def _(self, node: MatchExpr) -> Any:
        tag = node.op.kind
        if tag == "approx":
            return self.emit_approx(node)
        elif tag == "nearest":
            return self.emit_nearest(node)
        else:
            return self.emit_match(node)

    @adapt.register(GroupExpr)
    def _(self, node: GroupExpr) -> Any:
        with self._scoped_fields(fields=node.fields):
            return self.emit_group(node)

    @adapt.register(OutputSpecExpr)
    def _(self, node: OutputSpecExpr) -> Any:
        with self._scoped_output(node.target):
            return self.emit_output(node)

    @abstractmethod
    def emit_value(self, node: ValueExpr) -> Any: ...

    @abstractmethod
    def emit_date(self, node: DateExpr) -> Any: ...

    @abstractmethod
    def emit_binary(self, node: BinaryExpr) -> Any: ...

    def emit_not(self, node: UnaryExpr) -> Any:
        return self._format_negation(self.adapt(node.child))

    @classmethod
    def _format_negation(cls, value: str) -> str:
        return f"NOT {value}"

    @classmethod
    def _is_negation_of(cls, a: str, b: str) -> bool:
        return a == cls._format_negation(a) or b == cls._format_negation(a)

    def emit_query(self, ast_root: Query) -> QueryObject:
        return self._normalize(self.adapt(ast_root.body))

    def emit_group(self, node: GroupExpr) -> str:
        if self._handle_unsearchable_fields(node):
            return ""
        inner = self.adapt(node.child)
        if not inner:
            return ""

        return f"({inner})" if self._needs_parentheses(inner) else inner

    def emit_approx(self, node: MatchExpr) -> Any:
        return self.adapt(node.child)

    def emit_nearest(self, node: MatchExpr) -> Any:
        return self.adapt(node.child)

    def emit_match(self, node: MatchExpr) -> Any:
        return self.adapt(node.child)

    def emit_output(self, node: OutputSpecExpr) -> Any:
        return self._normalize(self.adapt(node.child))

    @classmethod
    def _is_fully_enclosed(cls, text: str) -> bool:
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

    @classmethod
    def _is_unsearchable(cls, field):
        return False

    @classmethod
    def _is_searchable(cls, field):
        return not cls._is_unsearchable(field)

    def _handle_unsearchable_fields(self, node) -> bool:
        fields = getattr(node, "fields", []) or self.field_ctx
        searchable = list(filter(self._is_searchable, fields))
        unsearchable = list(filter(self._is_unsearchable, fields))

        if len(unsearchable) == 0:
            return False

        pattern = self._create_regex(node)
        if pattern:
            self._regex_parts.append(pattern)
        node.fields = searchable

        return len(searchable) == 0

    @classmethod
    def _needs_parentheses(cls, s: str) -> bool:
        if not s:
            return False
        if BoolOp.AND not in s and BoolOp.OR not in s:
            return False
        return not cls._is_fully_enclosed(s)

    def _create_regex(self, node) -> str:
        """
        Recursively convert an AST subtree into a client-side regex pattern.

        AND  ->  left_pattern .+ right_pattern
        OR   ->  (v1|v2|…)  via _flatten_or
        NOT  ->  ""
        leaf -> _regex_atom(value)
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

    @classmethod
    def _merge_dicts(
        cls, left: dict, right: dict, merge_values: Callable[[Any, Any], Any]
    ) -> dict:
        """Merge two dictionaries using the ``merge_values`` criterion to merge keys that exist in both."""
        if left is None or right is None:
            return left or right

        result = left.copy()
        for key, value in right.items():
            if key not in left:
                result[key] = right[key]
                continue
            result[key] = merge_values(left[key], right[key])
        return result
