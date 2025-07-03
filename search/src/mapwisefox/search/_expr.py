from enum import StrEnum

from mapwisefox.search._enum import EvidenceAttributes


class LogicalOperators(StrEnum):
    AND = "and"
    OR = "or"


class Expr:
    pass


class StrExpr(Expr):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f'"{self.value})"'


class AttrExpr(StrExpr):
    def __init__(self, name, value):
        super().__init__(value)
        self.name = name

    def __str__(self):
        return f"{self.name}: {self.value}"

    def __repr__(self):
        return f"{self.name}: {self.value}"


class TitleExpr(AttrExpr):
    def __init__(self, value):
        super().__init__(EvidenceAttributes.TITLE, value)


class AbstractExpr(AttrExpr):
    def __init__(self, value):
        super().__init__(EvidenceAttributes.ABSTRACT, value)


class AuthorKeysExpr(AttrExpr):
    def __init__(self, value):
        super().__init__(EvidenceAttributes.KEYS, value)


class EvidenceTypeExpr(AttrExpr):
    def __init__(self, value):
        super().__init__(EvidenceAttributes.DOCTYPE, value)


class SubjectAreaExpr(AttrExpr):
    def __init__(self, value):
        super().__init__(EvidenceAttributes.SUBJECT, value)


class LanguageExpr(AttrExpr):
    def __init__(self, value):
        super().__init__(EvidenceAttributes.LANGUAGE, value)


class YearRangeExpr(Expr):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __str__(self):
        return f"(year BETWEEN {self.start} AND {self.end})"

    def __repr__(self):
        return f"(year BETWEEN {self.start} AND {self.end})"


class NaryExpr(Expr):
    def __init__(self, op, children, attr=None):
        self.op = op
        self.children = children
        self.attr = attr

    def add(self, child):
        self.children.append(child)
        return self

    def __str__(self):
        attr = f"[{self.attr}]" if self.attr else ""
        return f'{attr}({f" {self.op} ".join(map(str, self.children))})'

    def __repr__(self):
        attr = f"[{self.attr}]" if self.attr else ""
        return f'NaryExpr{attr}({f" {self.op} ".join(map(str, self.children))})'


class TitleAbsExpr(NaryExpr):
    def __init__(self, value):
        super().__init__(LogicalOperators.OR, [TitleExpr(value), AbstractExpr(value)])


class TitleAbsKeysExpr(NaryExpr):
    def __init__(self, value):
        super().__init__(
            LogicalOperators.OR,
            [TitleExpr(value), AbstractExpr(value), AuthorKeysExpr(value)],
        )


class EvidenceTypesExpr(NaryExpr):
    def __init__(self, *values):
        super().__init__(LogicalOperators.OR, list(map(EvidenceTypeExpr, values)))


class SubjectAreasExpr(NaryExpr):
    def __init__(self, *values):
        super().__init__(LogicalOperators.OR, list(map(SubjectAreaExpr, values)))


class LanguagesExpr(NaryExpr):
    def __init__(self, *values):
        super().__init__(LogicalOperators.OR, list(map(LanguageExpr, values)))


class MultipleKeysExpr(NaryExpr):
    def __init__(self, *values):
        super().__init__(LogicalOperators.OR, list(map(AuthorKeysExpr, values)))
