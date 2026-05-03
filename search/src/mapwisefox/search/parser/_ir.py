import sys
from dataclasses import dataclass, field
from enum import StrEnum
from typing import List

from lark import ast_utils

this_module = sys.modules[__name__]


class BoolOp(StrEnum):
    AND = "&"
    OR = "|"


class MatchType(StrEnum):
    STRICT = "strict"
    LOOSE = "loose"
    REGEX = "regex"


class OutputTarget(StrEnum):
    QUERY = "query"
    FILTER = "filter"
    BOTH = "both"


class _Ast(ast_utils.Ast):
    pass


@dataclass
class ValueExpr(_Ast):
    """value_expr: STRING"""

    value: str
    fields: list[str] = field(default_factory=list)


@dataclass
class FieldList(_Ast, ast_utils.AsList):
    """field_list: field_name ("," field_name)*"""

    items: List[str]


@dataclass
class AttrClause(_Ast):
    """attr_clause: "in" field_list"""

    field_list: FieldList


@dataclass
class BinaryExpr(_Ast):
    """binary_expr: expr boolean_op expr"""

    left: object  # DSLNode
    op: BoolOp
    right: object  # DSLNode
    fields: list[str] = field(default_factory=list)


@dataclass
class GroupExpr(_Ast):
    """group_expr: "(" expr ")" """

    child: object
    fields: list[str] = field(default_factory=list)


@dataclass
class UnaryExpr(_Ast):
    """unary_expr: "!" expr  |  match_expr"""

    child: object


@dataclass
class MatchExpr(_Ast):
    """match_expr: match_op "(" compound_expr ")" """

    op: object  # tuple produced by ToAst.match_op
    child: object


@dataclass
class OutputSpecExpr(_Ast):
    """output_spec_expr: "[" output_spec compound_expr "]" """

    target: OutputTarget
    child: object
