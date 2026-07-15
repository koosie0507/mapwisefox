from typing import Any

import arrow

from ._base import DSLAdapter
from ..parser import OutputSpecExpr, GroupExpr
from ..parser._ir import BinaryExpr, ValueExpr, DateExpr, BoolOp, Query
from ...query import QueryObject


class AcmDSLAdapter(DSLAdapter):
    _FIELD_MAP = {
        "title": "Title",
        "abstract": "Abstract",
        "keywords": "Keyword",
        "published": "E-Publication Date",
        "evidence_type": "Article Type",
    }
    _VALUE_MAP = {
        "evidence_type": {
            "article": "Research Article",
            "conference": "Research Article",
        }
    }
    _FILTER_FIELDS: set[str] = {"evidence_type", "language", "subject"}

    def __init__(self):
        super().__init__()
        self._filters = {}

    def emit_value(self, node: ValueExpr) -> Any:
        if self._handle_unsearchable_fields(node):
            return ""

        val = node.value
        fields = node.fields or self.field_ctx
        for f in fields:
            val = self._VALUE_MAP.get(f, {}).get(val, val)

        return (
            self._apply_fields(f'"{val}"', node.fields) if node.fields else f'"{val}"'
        )

    def emit_date(self, node: DateExpr) -> Any:
        lo = arrow.get(node.date_lo) if node.date_lo else None
        if lo and lo == lo.floor(frame="year"):
            lo = lo.floor(frame="year").format("MM/DD/YYYY")
        hi = arrow.get(node.date_hi) if node.date_hi else None
        if hi and hi == hi.floor(frame="year"):
            hi = hi.ceil(frame="year").format("MM/DD/YYYY")

        field_name = self._FIELD_MAP.get(node.field, node.field)
        if lo and hi:
            self._filters[field_name] = f"({lo} TO {hi})"
        elif lo:
            self._filters[field_name] = f"({lo} TO *)"
        elif hi:
            self._filters[field_name] = f"(* TO {hi})"

        return ""

    def emit_binary(self, node: BinaryExpr) -> Any:
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

    def emit_group(self, node: GroupExpr) -> str:
        expr = super().emit_group(node)
        return self._apply_fields(expr, node.fields) if node.fields else expr

    def emit_output(self, node: OutputSpecExpr) -> Any:
        return self.adapt(node.child)

    def emit_query(self, ast_root: Query) -> Any:
        result = self.adapt(ast_root.body)
        return QueryObject(query=result, filters=self._filters)

    def _apply_fields(self, expr: str, fields: list[str]) -> str:
        parts = []
        for f in fields:
            target_field_name = self._FIELD_MAP.get(f)
            if target_field_name is None:
                continue
            if f in self._FILTER_FIELDS:
                self._filters[target_field_name] = expr.strip('"')
            else:
                parts.append(f"{target_field_name}:{expr}")
        if not parts:
            return ""
        return " OR ".join(parts)
