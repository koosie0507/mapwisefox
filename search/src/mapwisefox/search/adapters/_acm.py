from mapwisefox.search import EvidenceAttributes, YearRangeExpr
from mapwisefox.search.adapters._expr_tree import ExprTreeAdapter


class ACMAdapter(ExprTreeAdapter):
    EVIDENCE_ATTR_MAP = {
        EvidenceAttributes.TITLE: "Title",
        EvidenceAttributes.ABSTRACT: "Abstract",
        EvidenceAttributes.KEYS: "Keyword",
        ExprTreeAdapter.YEAR_RANGE_KEY: "E-Publication Date",
    }
    UNSUPPORTED_ATTRS = {
        EvidenceAttributes.DOCTYPE,
        EvidenceAttributes.LANGUAGE,
        EvidenceAttributes.SUBJECT,
    }

    def _emit_expr(self, expr):
        if isinstance(expr, YearRangeExpr):
            return f"(01/01/{expr.start:04} TO 31/12/{expr.end:04})"
        return super()._emit_expr(expr)

    def _emit_factored(self, root_op, expr_dict):
        disjunctive_attrs = self.UNSUPPORTED_ATTRS | {
            EvidenceAttributes.TITLE,
            EvidenceAttributes.ABSTRACT,
        }
        basic_clauses = f" {root_op.upper()} ".join(
            f"({self.EVIDENCE_ATTR_MAP.get(key, key)}: {self._emit_expr(expr)})"
            for key, expr in expr_dict.items()
            if key not in disjunctive_attrs and key != self.YEAR_RANGE_KEY
        )
        title = expr_dict[EvidenceAttributes.TITLE]
        abstract = expr_dict[EvidenceAttributes.ABSTRACT]
        title_abstract = f"(Title: { self._emit_expr(title) } OR Abstract: { self._emit_expr(abstract) })"
        return {
            "query": f" {root_op.upper()} ".join([title_abstract, basic_clauses]),
            "filter": {
                self.EVIDENCE_ATTR_MAP[key]: self._emit_expr(value)
                for key, value in expr_dict.items()
                if key in {self.YEAR_RANGE_KEY}
            },
        }

    def _map_expr_tuples(self, expr_tuples):
        return (
            (self.EVIDENCE_ATTR_MAP.get(key, key), expr) for key, expr in expr_tuples
        )

    def _filter_expr_tuples(self, expr_tuples):
        return (
            (key, expr)
            for key, expr in expr_tuples
            if key not in self.UNSUPPORTED_ATTRS
        )
