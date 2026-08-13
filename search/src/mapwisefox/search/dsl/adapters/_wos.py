from typing import Any
import arrow
from mapwisefox.search.query import QueryObject
from ._base import DSLAdapter
from ..parser._ir import (
    BinaryExpr,
    BoolOp,
    DateExpr,
    ValueExpr,
    NearExpr,
    GroupExpr,
    Query,
    OutputTarget,
)


class WebOfScienceDSLAdapter(DSLAdapter):
    _DATE_FORMAT_STRING = "YYYY-MM-DD"
    _FIELD_MAP = {
        "title": "TI",
        "abstract": "AB",
        "keywords": "AK",
        "evidence_type": "DT",
        "subject": "WC",
        "language": "LA",
        "published": "DOP",
    }
    _VALUE_MAP = {
        "evidence_type": {
            "article": "Article",
        },
        "subject": {
            "computer science": "Computer Science",
        },
        "language": {
            "english": "English",
        },
    }

    def emit_value(self, node: ValueExpr) -> Any:
        val = node.value
        fields = node.fields or self.field_ctx
        fields_with_vals = [f for f in fields if f in self._VALUE_MAP]
        if fields_with_vals:
            values = dict.fromkeys(
                self._VALUE_MAP[f][val]
                for f in fields_with_vals
                if val in self._VALUE_MAP[f]
            )
            if len(values) == 0:
                return ""
            val = next(iter(values))
        val = f'"{val.strip('"')}"'

        if self.output_ctx == OutputTarget.QUERY:
            expr_fields = node.fields
            expr = QueryObject(query=val)
        else:
            expr_fields = fields
            filters = {field: [val] for field in expr_fields}
            expr = QueryObject(filters=filters)
        return self._apply_fields(expr, expr_fields)

    def emit_near(self, node: NearExpr) -> Any:
        """Translate ``near[n](a, b)`` to the native ``NEAR/n`` operator."""
        term = f'("{node.left.value}" NEAR/{node.distance} "{node.right.value}")'
        fields = node.fields or self.field_ctx

        if self.output_ctx == OutputTarget.QUERY:
            expr_fields = node.fields
            expr = QueryObject(query=term)
        else:
            expr_fields = fields
            filters = {field: [term] for field in expr_fields}
            expr = QueryObject(filters=filters)
        return self._apply_fields(expr, expr_fields)

    def emit_date(self, node: DateExpr) -> Any:
        field_name = self._FIELD_MAP.get(node.field, node.field.upper())
        lo = arrow.get(node.date_lo)
        lo_fmt = lo.format(self._DATE_FORMAT_STRING)
        hi = arrow.get(node.date_hi)
        if hi == hi.floor(frame="year"):
            hi = hi.ceil(frame="year")
        hi_fmt = hi.format(self._DATE_FORMAT_STRING)

        expr = ""
        match node.op:
            case "after":
                expr = f"{lo_fmt}/{arrow.now().format(self._DATE_FORMAT_STRING)}"
            case "before":
                expr = f"1950-01-01/{hi_fmt}"
            case "between":
                expr = f"{lo_fmt}/{hi_fmt}"
            case _:
                raise ValueError(f"Unknown date operator: {node.op!r}")
        return self._emit_leaf_target(field_name, expr)

    def emit_binary(self, node: BinaryExpr) -> Any:
        left = self._normalize(self.adapt(node.left))
        right = self._normalize(self.adapt(node.right))

        op = "AND" if node.op == BoolOp.AND else "OR"
        if left.query and right.query:
            if op == "AND" and right.query.startswith("NOT"):
                query_str = f"{left.query} {right.query}"
            elif op == "AND" and left.query.startswith("NOT"):
                query_str = f"{right.query} {left.query}"
            else:
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

        expr = QueryObject(query=query_str, filters=filters)
        return self._apply_fields(expr, node.fields)

    def emit_group(self, node: GroupExpr) -> QueryObject:
        inner = self._normalize(self.adapt(node.child))
        query_str = inner.query
        if query_str and not self._is_fully_enclosed(query_str):
            query_str = f"({query_str})"
        return self._apply_fields(
            QueryObject(query=query_str, filters=inner.filters), node.fields
        )

    def emit_query(self, ast_root: Query) -> QueryObject:
        """Top-level method to generate the final Scopus string."""
        result = self._normalize(self.adapt(ast_root.body))
        filter_clauses = [
            self._enclose_field(attr, filter_clause) if attr else filter_clause
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

    def _enclose_field(self, field: str, s: str) -> str:
        if self._is_fully_enclosed(s):
            return f"{field}={s}"
        return f"{field}=({s})"

    def _apply_fields(self, expr: QueryObject, fields: list[str]) -> QueryObject:
        if not fields:
            return expr

        fields = [f for f in dict.fromkeys(fields)]
        sd_fields = [self._FIELD_MAP.get(f) for f in fields]

        if self.output_ctx == OutputTarget.QUERY:
            if expr.query:
                expr.query = " OR ".join(
                    self._enclose_field(f, expr.query) for f in sd_fields
                )
            if len(sd_fields) > 1:
                expr.query = f"({expr.query})"
        if self.output_ctx == OutputTarget.FILTER:
            filters = {}
            for orig_field, sd_field in zip(fields, sd_fields):
                if sd_field is None:
                    continue
                orig_field_filters = expr.filters.get(orig_field, [])
                sd_field_filters = expr.filters.get(sd_field, [])
                filters[sd_field] = self._merge_filters(
                    orig_field_filters, sd_field_filters
                )
            expr.filters = filters

        return expr
