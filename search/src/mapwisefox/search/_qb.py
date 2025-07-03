from mapwisefox.search._expr import (
    LogicalOperators,
    YearRangeExpr,
    NaryExpr,
    EvidenceTypeExpr,
    SubjectAreaExpr,
    SubjectAreasExpr,
    EvidenceTypesExpr,
    LanguageExpr,
    LanguagesExpr,
    AuthorKeysExpr,
    MultipleKeysExpr,
)


class QueryBuilder:
    def __init__(self):
        self._expr_tree = NaryExpr(LogicalOperators.AND, [])

    @staticmethod
    def and_group(*children):
        return NaryExpr(LogicalOperators.AND, children)

    @staticmethod
    def or_group(*children):
        return NaryExpr(LogicalOperators.OR, children)

    def groups(self, *groups):
        for g in groups:
            self._expr_tree.add(g)
        return self

    def year_range(self, year_start, year_end):
        self._expr_tree.add(YearRangeExpr(year_start, year_end))
        return self

    def _add_one_or_more(self, cls_one, cls_more, values):
        if len(values) < 1:
            return self

        expr = cls_one(values[0]) if len(values) == 1 else cls_more(*values)
        self._expr_tree.add(expr)
        return self

    def subject_areas(self, *values):
        return self._add_one_or_more(SubjectAreaExpr, SubjectAreasExpr, values)

    def doc_types(self, *values):
        return self._add_one_or_more(EvidenceTypeExpr, EvidenceTypesExpr, values)

    def languages(self, *values):
        return self._add_one_or_more(LanguageExpr, LanguagesExpr, values)

    def keywords(self, *values):
        return self._add_one_or_more(AuthorKeysExpr, MultipleKeysExpr, values)

    def __str__(self):
        return str(self._expr_tree)

    def __repr__(self):
        return str(self._expr_tree)

    @staticmethod
    def _visit(visitor, item):
        if isinstance(item, NaryExpr):
            visitor.visit_start_group(item)
            for child in item.children:
                QueryBuilder._visit(visitor, child)
            visitor.visit_end_group(item)
        else:
            visitor.visit_term(item)

    def build(self, adapter_type):
        visitor_instance = adapter_type()
        self._visit(visitor_instance, self._expr_tree)
        return visitor_instance.result()
