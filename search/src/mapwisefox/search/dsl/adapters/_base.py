import re as _re
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from functools import singledispatchmethod, partial
from typing import Any, Callable

from mapwisefox.search.query import QueryObject
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
    MatchType,
)


class DSLAdapter(metaclass=ABCMeta):
    _REGEX_NORM_KEY = "regex"

    def __init__(self):
        self._field_ctx_stack: list[list[str]] = []
        self._output_ctx_stack: list[OutputTarget] = []
        self._regex_parts: list[str] = []

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

    @singledispatchmethod
    def adapt(self, node: Any) -> Any:
        raise TypeError(f"No adapter registered for IR node type: {type(node)!r}")

    @adapt.register(Query)
    def _(self, node: Query) -> Any:
        return self.emit_query(node)

    @adapt.register(ValueExpr)
    def _(self, node: ValueExpr) -> Any:
        return self._emit_node_with_regex_handling(node, self.emit_value)

    @adapt.register(DateExpr)
    def _(self, node: DateExpr) -> Any:
        return self._emit_node_with_regex_handling(node, self.emit_date)

    @adapt.register(BinaryExpr)
    def _(self, node: BinaryExpr) -> Any:
        return self._emit_node_with_regex_handling(node, self.emit_binary)

    @adapt.register(UnaryExpr)
    def _(self, node: UnaryExpr) -> Any:
        with self._scoped_fields(fields=node.fields):
            return self._emit_node_with_regex_handling(node, self.emit_not)

    @adapt.register(MatchExpr)
    def _(self, node: MatchExpr) -> Any:
        with self._scoped_fields(fields=node.fields):
            tag = node.op.kind
            if tag == "approx":
                return self._emit_node_with_regex_handling(node, self.emit_approx)
            elif tag == "nearest":
                return self._emit_node_with_regex_handling(node, self.emit_nearest)
            else:
                return self._emit_node_with_regex_handling(node, self.emit_match)

    @adapt.register(GroupExpr)
    def _(self, node: GroupExpr) -> Any:
        with self._scoped_fields(fields=node.fields):
            return self._emit_node_with_regex_handling(node, self.emit_group)

    @adapt.register(OutputSpecExpr)
    def _(self, node: OutputSpecExpr) -> Any:
        with self._scoped_output(node.target):
            return self.emit_output(node)

    @abstractmethod
    def emit_value(self, node: ValueExpr) -> QueryObject: ...

    @abstractmethod
    def emit_date(self, node: DateExpr) -> QueryObject: ...

    def emit_binary(self, node: BinaryExpr) -> QueryObject:
        left = self._normalize(self.adapt(node.left))
        right = self._normalize(self.adapt(node.right))

        query = self._merge_binary_query(left.query, right.query, node.op)
        filters = self._merge_dicts(
            left.filters, right.filters, self._merge_filter_clauses
        )
        merge_patterns = partial(self.__merge_regex_patterns, op=node.op)
        regex = self._merge_dicts(left.regex, right.regex, merge_patterns)

        return QueryObject(query=query, regex=regex, filters=filters)

    def _merge_binary_query(self, left: str, right: str, op: BoolOp) -> str:
        if not left and not right:
            return ""
        if not left:
            return right
        if not right:
            return left

        if self._is_negation_of(left, right):
            if op == BoolOp.AND:
                return ""
            if op == BoolOp.OR:
                return left if self._format_negation(left) != left else right

        return f"{left} {self._map_bool_op(op)} {right}"

    @classmethod
    def _map_bool_op(cls, op: BoolOp) -> str:
        match op:
            case BoolOp.AND:
                return "and"
            case BoolOp.OR:
                return "or"
        raise ValueError(f"unsupported binary operation {op}")

    def emit_not(self, node: UnaryExpr) -> QueryObject:
        inner = self.adapt(node.child)
        inner.query = self._format_negation(inner.query)
        return inner

    def emit_approx(self, node: MatchExpr) -> QueryObject:
        return self.adapt(node.child)

    def emit_nearest(self, node: MatchExpr) -> QueryObject:
        return self.adapt(node.child)

    def emit_match(self, node: MatchExpr) -> QueryObject:
        """Handle ``match[type]`` syntax nodes.

        The handling of these nodes passes through for ``strict`` and ``loose``
        match policies. Those must be handled according to each backend's rules.
        The same does not apply by default for ``regex`` matches which signal
        the user's intent to match each retrieved item against the provided
        pattern on the client, post-retrieval. Changing this behavior for any
        backend must be documented accordingly.
        """
        match node.op.arg:
            case MatchType.REGEX:
                pattern = self.__extract_raw_regex(node)
                fields = self._get_all_node_fields(node)
                regex_dict = (
                    {field: pattern for field in fields} if fields else {"": pattern}
                )
                return QueryObject(regex=regex_dict)
            case _:
                return self.adapt(node.child)

    def emit_group(self, node: GroupExpr) -> QueryObject:
        inner = self._normalize(self.adapt(node.child)) or QueryObject()
        if inner.query and self._needs_parentheses(inner.query):
            inner.query = f"({inner.query})"
        return inner

    def emit_output(self, node: OutputSpecExpr) -> QueryObject:
        inner_expr = self._normalize(self.adapt(node.child))
        if self._needs_parentheses(inner_expr.query):
            inner_expr.query = f"({inner_expr.query})"
        return inner_expr

    def emit_query(self, ast_root: Query) -> QueryObject:
        return self._normalize(self.adapt(ast_root.body))

    def _emit_leaf_target(self, prefix: str, expr: str) -> QueryObject:
        """Emit a ``QueryObject`` for a leaf syntax node.

        This method is called by `emit_value`, `emit_date`, `emit_not`,
        `emit_approx`, `emit_nearest`, `emit_match`.
        """
        match self.output_ctx:
            case OutputTarget.QUERY:
                emitted = f"{prefix}({expr})" if prefix else expr
                return QueryObject(query=emitted)
            case OutputTarget.FILTER:
                return QueryObject(filters={prefix: [expr]})

    def _emit_leaf_targets(self, fields: list[str], expr: str) -> QueryObject:
        """Emit a ``QueryObject`` for a leaf syntax node.

        It applies the requested fields to the expression using
        ``self._apply_fields``. It uses the nearest scope's ``OutputTarget``.
        """
        query_fields = list(filter(self._is_query_field, fields))
        filter_fields = list(filter(self._is_filter_field, fields))
        if self.output_ctx == OutputTarget.QUERY and query_fields:
            return QueryObject(query=expr)
        return QueryObject(filters={field: [expr] for field in filter_fields})

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

    def _get_all_node_fields(self, node: Any) -> list[str]:
        return getattr(node, "fields", None) or self.field_ctx

    @classmethod
    def _is_field_supported(cls, field: str) -> bool:
        """Is true if the field is supported by the adapter.

        Allows subclasses to skip unsupported fields from the output.
        """
        return True

    @classmethod
    def _map_field_name(cls, field: str) -> str:
        """Map field name to target."""
        return field

    def _is_filter_field(self, field: str) -> bool:
        """Is true if a field must be handled as a filter regardless of the output target."""
        return self.output_ctx == OutputTarget.FILTER and self._is_field_supported(
            field
        )

    def _is_query_field(self, field: str) -> bool:
        return (
            self.output_ctx == OutputTarget.QUERY
            and self._is_field_supported(field)
            and not self._is_filter_field(field)
        )

    def _map_field_names(self, fields: list[str]) -> list[str]:
        """Map a list of field names to a list of target field names.

        By default, we map each source field name to a target field name by using
        ``self._map_field_name``. This method allows changing the default behavior
        by compressing multiple input field names to a compound field name, for
        example.
        """
        return list(map(self._map_field_name, fields))

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

    @abstractmethod
    def _enclose_field(self, field: str, query: str) -> str: ...

    def _apply_fields(self, inner: QueryObject, fields: list[str]) -> QueryObject:
        if not fields:
            return inner

        fields = [f for f in dict.fromkeys(fields) if self._is_field_supported(f)]

        query_fields = list(filter(self._is_query_field, fields))
        if self.output_ctx == OutputTarget.QUERY:
            targets = self._map_field_names(query_fields)
            if inner.query:
                inner.query = f" {self._map_bool_op(BoolOp.OR)} ".join(
                    self._enclose_field(name, inner.query) for name in targets
                )
                if len(targets) > 1:
                    inner.query = f"({inner.query})"

        # filters must be updated for all output targets
        filter_fields = list(filter(self._is_filter_field, fields))
        targets = self._map_field_names(filter_fields)
        filters = {}
        for original, target in zip(filter_fields, targets):
            if target is None:
                continue
            orig_clauses = inner.filters.get(original, [])
            target_clauses = inner.filters.get(target, [])
            filters[target] = self._merge_filter_clauses(orig_clauses, target_clauses)
            inner.filters = filters
        return inner

    @classmethod
    def _format_negation(cls, value: str) -> str:
        """Format the input value as its negation."""
        return f"NOT {value}"

    @classmethod
    def _is_negation_of(cls, a: str, b: str) -> bool:
        """Determine whether either one of the arguments is a negation of the other."""
        return a == cls._format_negation(a) or b == cls._format_negation(a)

    @classmethod
    def _is_fully_enclosed(cls, text: str) -> bool:
        """
        Check if the input is fully enclosed by a single pair of parentheses.

        Flags groups like ``'(A OR B)'``, but not ``'(A) OR (B)'``.
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
    def _needs_parentheses(cls, s: str) -> bool:
        """Determine whether the input should be wrapped in parentheses.

        An empty string should not be wrapped. A string that doesn't contain
        a binary operation should also not be wrapped. Lastly, if the string
        is already fully enclosed in parentheses, it shouldn't be wrapped.
        """
        if not s:
            return False
        and_str = cls._map_bool_op(BoolOp.AND)
        or_str = cls._map_bool_op(BoolOp.OR)
        if and_str not in s and or_str not in s:
            return False
        return not cls._is_fully_enclosed(s)

    @classmethod
    def _merge_dicts(
        cls, left: dict, right: dict, merge_values: Callable[[Any, Any], Any]
    ) -> dict:
        """Merge two dictionaries using the ``merge_values`` criterion.

        The algorithm creates an algorithm that contains the unique keys from
        both input dictionaries. The values for the keys that exist in both
        input dictionaries are the result of applying the ``merge_values``
        callback to the input values.

        :param left: left operand
        :param right: right operand
        :param merge_values: callback that merges the ``left`` values with the
           ``right`` values stored under the same key in both input dictionaries.
        """
        if left is None or right is None:
            return left or right

        result = left.copy()
        for key, value in right.items():
            if key not in left:
                result[key] = value
                continue
            result[key] = merge_values(left[key], value)
        return result

    @staticmethod
    def _merge_filter_clauses(
        left_clauses: list[str], right_clauses: list[str]
    ) -> list[str]:
        return [
            filter_clause
            for filter_clause in dict.fromkeys(left_clauses + right_clauses)
            if filter_clause is not None and len(filter_clause.strip()) > 0
        ]

    # -- REGEX handling -------------------------------------------------------

    def _emit_node_with_regex_handling(
        self, node: Any, emit_inner: Callable
    ) -> QueryObject:
        """Handle groups of nested statements.

        Whenever a group is encountered, the fields that cannot be handled by
        the backend must be peeled away first. The default handling for these
        fields is to translate the search clauses to regular expressions that
        are evaluated on the client post-retrieval.
        """
        regex_dict, passthrough_fields = self._handle_regex_fields(node)
        has_own_fields = bool(getattr(node, "fields", None))
        if passthrough_fields and has_own_fields:
            # update direct field qualifiers
            node.fields = passthrough_fields

        if passthrough_fields or not has_own_fields:
            # there are either fields that are not regex fields OR
            # there aren't any field qualifiers for this particular group
            inner = self._normalize(emit_inner(node))
        else:
            # no pass-through and was directly qualified with fields
            inner = QueryObject()

        if regex_dict:
            inner.regex = {**inner.regex, **regex_dict}

        return inner

    def _is_regex_field(self, field: str) -> bool:
        """Determine whether to handle the field as a client side regex."""
        return False

    def _is_searchable(self, field):
        """Opposite of ``_is_unsearchable()``."""
        return not self._is_regex_field(field)

    def _regex_fields(self, node: Any) -> list[str]:
        return list(filter(self._is_regex_field, self._get_all_node_fields(node)))

    def _handle_regex_fields(self, node: Any) -> tuple[dict[str, str], list[str]]:
        """Create regex expressions for all unsearchable node fields.

        If the node declares explicit fields (i.e. it is the syntax node with
        the attached ``in field1, field2`` qualifier) then the directly
        attributed fields are used. If it doesn't (i.e. it's a nested node of
        the node with the qualifier) then the fields declared in the node's
        current scope are used. This allows value nodes (which are usually
        grouped or combined through binary expressions) to be interpreted in
        the context of their 'parent' nodes.

        The fields are divided into passthrough fields and regex fields. The
        passthrough fields are handled downstream. For each regex field, though,
        we must return a resulting regex.
        """
        fields = self._get_all_node_fields(node)
        passthrough_fields = list(filter(self._is_searchable, fields))
        regex_fields = self._regex_fields(node)

        if len(regex_fields) == 0:
            return {}, passthrough_fields

        pattern = self._extract_regex_pattern(node)
        regex_dict = {field: pattern for field in regex_fields} if pattern else {}

        return regex_dict, passthrough_fields

    def _extract_regex_pattern(self, node: Any) -> str:
        """Return the regex pattern for ``node``.

        For ``match[regex]`` nodes the inner value is a raw user-supplied
        pattern that must be used verbatim.  For all other node types the
        pattern is built by ``_create_regex``, which applies ``_regex_atom``
        to escape DSL values and expand glob wildcards.
        """
        return (
            self.__extract_raw_regex(node)
            if isinstance(node, MatchExpr) and node.op.arg == "regex"
            else self._create_regex(node)
        )

    @classmethod
    def __extract_raw_regex(cls, node: MatchExpr) -> str:
        assert isinstance(node.child, ValueExpr), "missing ValueExpr to match against"
        return node.child.value

    def _create_regex(self, node: Any) -> str:
        """Create a regular expression from the current node."""
        positive, lookaheads = self.__create_regex_inner(node)
        if not positive and not lookaheads:
            return ""

        lookaheads = "".join(lookaheads)
        if "|" in positive and not self._is_fully_enclosed(positive):
            positive = f"({positive})"
        return (
            f"^{lookaheads}{positive}"
            if lookaheads or "(?" in positive
            else f"{lookaheads}{positive}"
        )

    def __create_regex_inner(self, node: Any) -> tuple[str, list[str]]:
        match node:
            case GroupExpr():
                return self.__create_regex_inner(node.child)
            case MatchExpr():
                if node.op.arg == "regex":
                    return self._extract_regex_pattern(node), []
                return self.__create_regex_inner(node.child)
            case BinaryExpr():
                l_match, l_look = self.__create_regex_inner(node.left)
                r_match, r_look = self.__create_regex_inner(node.right)
                combined = ""
                if l_match and r_match:
                    if node.op == BoolOp.AND:
                        l_pos = self.__prepare_regex_and_operand(l_match.lstrip("^"))
                        l_look.append(f"(?=.*{l_pos})" if "(?" not in l_pos else l_pos)
                        r_pos = self.__prepare_regex_and_operand(r_match.lstrip("^"))
                        r_look.append(f"(?=.*{r_pos})" if "(?" not in r_pos else r_pos)
                    else:
                        combined = f"{l_match}|{r_match}"
                else:
                    combined = l_match or r_match
                return combined, l_look + r_look
            case UnaryExpr():
                # ensure we're operating with the expected version of the grammar
                assert isinstance(
                    node.child, ValueExpr
                ), "negations work only on value expressions"
                atom = self._regex_atom(node.child.value)
                return "", [f"(?!.*{atom})"]
            case ValueExpr():
                return self._regex_atom(node.value), []
        return "", []

    @staticmethod
    def _regex_atom(value: str) -> str:
        """Convert a DSL string (possible containing glob wildcards) to a regex atom.

        All regex-special characters are escaped first, then the escaped
        wildcards are replaced with their regular expression equivalents. More
        specifically, `\\*` is replaced with `.*` and ``\\?`` is replaced with
        `.?`."""
        return (
            _re.escape(value)
            .replace(r"\*", "\\w*")
            .replace(r"\?", "\\w?")
            .replace(r"\+", ".+")
            .replace(r"\(", "(")
            .replace(r"\)", ")")
            .replace(r"\ ", "\\s")
        )

    @classmethod
    def __merge_regex_patterns(cls, left_pat: str, right_pat: str, op: BoolOp) -> str:
        left_pat = left_pat.lstrip("^")
        right_pat = right_pat.lstrip("^")
        match op:
            case BoolOp.AND:
                left = cls.__prepare_regex_and_operand(left_pat)
                right = cls.__prepare_regex_and_operand(right_pat)
                return f"^{left}{right}"
            case BoolOp.OR:
                return f"^(?:{left_pat}|{right_pat})"
        raise ValueError(f"can't merge regex patterns invalid bool op '{op}'")

    @classmethod
    def __prepare_regex_and_operand(cls, pattern: str) -> str:
        if pattern.startswith("(?"):
            return pattern
        if "|" in pattern and not cls._is_fully_enclosed(pattern):
            pattern = f"({pattern})"
        return f"(?=.*{pattern})"
