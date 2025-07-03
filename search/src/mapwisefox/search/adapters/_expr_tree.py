from collections import defaultdict

from mapwisefox.search import YearRangeExpr
from mapwisefox.search._expr import NaryExpr, AttrExpr
from mapwisefox.search.adapters._base import QueryBuilderAdapter


class ExprTreeAdapter(QueryBuilderAdapter):
    YEAR_RANGE_KEY = "publication year range"

    def __init__(self):
        super().__init__()
        self._stack = []  # stack of lists of children
        self._root = None

    def visit_start_group(self, group):
        self._stack.append([])  # start a new child list

    def visit_term(self, term):
        self._stack[-1].append(term)

    def _process_current_buffer(self, children, group):
        node = NaryExpr(group.op, children)
        if self._stack:
            self._stack[-1].append(node)
        else:
            self._root = node

    @classmethod
    def _filter_by_key(cls, expr, target_key):
        if isinstance(expr, AttrExpr):
            return expr if expr.name == target_key else None
        elif isinstance(expr, YearRangeExpr):
            return expr if target_key == cls.YEAR_RANGE_KEY else None
        elif isinstance(expr, NaryExpr):
            new_children = []
            for child in expr.children:
                filtered = cls._filter_by_key(child, target_key)
                if filtered is None:
                    continue
                new_children.append(filtered)
            if len(new_children) == 0:
                return None
            elif len(new_children) == 1:
                return new_children[0]
            else:
                return NaryExpr(expr.op, new_children, attr=target_key)
        else:
            return None

    @classmethod
    def __extract_keys(cls, expr):
        keys = defaultdict(int)
        if isinstance(expr, AttrExpr):
            keys[expr.name] += 1
        if isinstance(expr, YearRangeExpr):
            keys[cls.YEAR_RANGE_KEY] += 1
        elif isinstance(expr, NaryExpr):
            for child in expr.children:
                for key in cls.__extract_keys(child):
                    keys[key] += 1
        return list(keys)

    @classmethod
    def __factor_by_key(cls, expr):
        keys = cls.__extract_keys(expr)
        result = {}
        for key in keys:
            filtered = cls._filter_by_key(expr, key)
            if not filtered:
                continue
            result[key] = filtered
        return result

    def _format_attr(self, attr_expr):
        return f'"{attr_expr.value.strip()}"'

    def _format_group(self, group):
        op = f" {group.op.upper()} "
        child_strings = [
            value for value in map(self._emit_expr, group.children) if value is not None
        ]
        if len(child_strings) == 0:
            return None
        if len(child_strings) == 1:
            return child_strings[0]

        return f"({op.join(child_strings)})"

    def _emit_expr(self, expr):
        if isinstance(expr, AttrExpr):
            return self._format_attr(expr)
        elif isinstance(expr, NaryExpr):
            return self._format_group(expr)
        else:
            return str(expr)  # catch-all

    def _emit_factored(self, root_op, expr_dict):
        return f" {root_op.upper()} ".join(
            f"({key}: {self._emit_expr(expr)})" for key, expr in expr_dict.items()
        )

    def result(self):
        factored = self.__factor_by_key(self._root)
        return self._emit_factored(self._root.op, factored)
