from mapwisefox.search import (
    EvidenceAttributes,
    EvidenceTypeExpr,
    EvidenceTypes,
    SubjectAreaExpr,
    SubjectAreas,
    LanguageExpr,
    YearRangeExpr,
)
from mapwisefox.search.adapters._expr_tree import ExprTreeAdapter


class WebOfScienceAdapter(ExprTreeAdapter):
    EVIDENCE_ATTR_MAP = {
        EvidenceAttributes.TITLE: "TI",
        EvidenceAttributes.ABSTRACT: "AB",
        EvidenceAttributes.KEYS: "AK",
        EvidenceAttributes.DOCTYPE: "DT",
        EvidenceAttributes.SUBJECT: "WC",
        EvidenceAttributes.LANGUAGE: "LA",
        ExprTreeAdapter.YEAR_RANGE_KEY: "PY",
    }

    EVIDENCE_TYPE_MAP = {
        EvidenceTypes.ARTICLE: "Article",
    }

    SUBJECT_AREA_MAP = {
        SubjectAreas.COMPUTER_SCIENCE: "Computer Science",
    }

    LANGUAGE_MAP = {
        "english": "English",
    }

    def __init__(self, use_starter_api=False):
        super(WebOfScienceAdapter, self).__init__()

    def _emit_expr(self, expr):
        if isinstance(expr, EvidenceTypeExpr):
            return self.EVIDENCE_TYPE_MAP.get(expr.value)
        base_expr_str = super()._emit_expr(expr)
        if isinstance(expr, SubjectAreaExpr) or isinstance(expr, LanguageExpr):
            return f"({base_expr_str})"
        if isinstance(expr, YearRangeExpr):
            return f"({expr.start}-{expr.end})"
        return base_expr_str

    def _format_attr(self, attr_expr):
        if isinstance(attr_expr, SubjectAreaExpr):
            return self.SUBJECT_AREA_MAP.get(attr_expr.value)
        elif isinstance(attr_expr, LanguageExpr):
            return self.LANGUAGE_MAP.get(attr_expr.value)
        if any(x in attr_expr.value for x in ("?", "*")):
            return attr_expr.value
        if " " not in attr_expr.value:
            return attr_expr.value
        return super()._format_attr(attr_expr)

    def _emit_factored(self, root_op, expr_dict):
        disjunctive_attrs = {
            EvidenceAttributes.TITLE,
            EvidenceAttributes.ABSTRACT,
        }
        basic_clauses = f" {root_op.upper()} ".join(
            f"{self.EVIDENCE_ATTR_MAP.get(key, key)}={self._emit_expr(expr)}"
            for key, expr in expr_dict.items()
            if key not in disjunctive_attrs
        )
        title = expr_dict[EvidenceAttributes.TITLE]
        abstract = expr_dict[EvidenceAttributes.ABSTRACT]
        title_abstract = (
            f"(TI={ self._emit_expr(title) } OR AB={ self._emit_expr(abstract) })"
        )

        return f" {root_op.upper()} ".join([title_abstract, basic_clauses])

    def _map_expr_tuples(self, expr_tuples):
        return (
            (self.EVIDENCE_ATTR_MAP.get(key, key), expr) for key, expr in expr_tuples
        )
