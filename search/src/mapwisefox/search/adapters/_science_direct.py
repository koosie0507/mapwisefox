from mapwisefox.search import (
    EvidenceAttributes,
    EvidenceTypes,
    YearRangeExpr,
    EvidenceTypeExpr,
)
from mapwisefox.search.adapters._expr_tree import ExprTreeAdapter


class ScienceDirectAdapter(ExprTreeAdapter):
    ATTR_MAP = {
        EvidenceAttributes.TITLE: "TITLE",
        EvidenceAttributes.ABSTRACT: "ABSTRACT",
        EvidenceAttributes.KEYS: "KEYWORDS",
        EvidenceAttributes.DOCTYPE: "CONTENT-TYPE",
    }
    DOCTYPE_MAP = {
        EvidenceTypes.ARTICLE: "JL",
    }

    def __init__(self):
        super().__init__()

    def _emit_expr(self, expr):
        if isinstance(expr, YearRangeExpr):
            return f"(PUB-DATE AFT {expr.start:04}0101 AND PUB-DATE BEF {expr.end}0701)"
        elif isinstance(expr, EvidenceTypeExpr):
            return f"({self.DOCTYPE_MAP.get(expr.value)})"
        return super()._emit_expr(expr)

    def _emit_factored(self, root_op, expr_dict):
        disjunctive_attrs = {
            EvidenceAttributes.TITLE,
            EvidenceAttributes.ABSTRACT,
            self.YEAR_RANGE_KEY,
            EvidenceAttributes.SUBJECT,
            EvidenceAttributes.LANGUAGE,
        }
        basic_clauses = f" {root_op.upper()} ".join(
            f"{self.ATTR_MAP.get(key)}{self._emit_expr(expr)}"
            for key, expr in expr_dict.items()
            if key not in disjunctive_attrs and key in self.ATTR_MAP
        )
        title = expr_dict[EvidenceAttributes.TITLE]
        abstract = expr_dict[EvidenceAttributes.ABSTRACT]
        title_abstract = f"(TITLE{ self._emit_expr(title) } OR ABSTRACT{ self._emit_expr(abstract) })"
        clauses = [title_abstract, basic_clauses]
        if self.YEAR_RANGE_KEY in expr_dict:
            clauses.append(self._emit_expr(expr_dict[self.YEAR_RANGE_KEY]))
        return f" {root_op.upper()} ".join(clauses)

    def result(self):
        return {
            "query": super().result(),
        }
