"""Intermediate representation for the search DSL.

Each AST node is a dataclass discoverable by `lark.ast_utils.create_transformer`.
Nodes that may carry an `attr_clause` (field list) expose a `fields: list[str]`
attribute populated by the transformer in `_parser.py`.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from lark import ast_utils
from lark.tree import Meta


class _Ast(ast_utils.Ast):
    """Marker base. `create_transformer` discovers all subclasses in this module."""

    pass


class _AstWithMeta(ast_utils.Ast, ast_utils.WithMeta):
    """Variant that retains source-position metadata."""

    meta: Meta


class BoolOp(str, Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class MatchType(str, Enum):
    STRICT = "strict"
    LOOSE = "loose"
    REGEX = "regex"


class OutputTarget(str, Enum):
    QUERY = "query"
    FILTER = "filter"
    BOTH = "both"


@dataclass
class FieldList(_Ast, ast_utils.AsList):
    """`title, abstract, keywords` → FieldList(items=['title','abstract','keywords'])"""

    items: List[str]


@dataclass
class AttrClause(_Ast):
    """`in <FieldList>` — consumed by the transformer; never appears in final AST."""

    field_list: FieldList


@dataclass
class MatchOp(_Ast):
    """Wraps a match operator and its optional argument(s)."""

    kind: str  # 'approx' | 'nearest' | 'match'
    arg: Optional[object] = None  # int for nearest, MatchType for match


@dataclass
class ValueExpr(_Ast):
    value: str  # raw, unquoted
    fields: List[str] = field(default_factory=list)


@dataclass
class MatchExpr(_Ast):
    op: MatchOp
    child: object
    fields: List[str] = field(default_factory=list)


@dataclass
class UnaryExpr(_Ast):
    op: BoolOp  # NOT
    child: object
    fields: List[str] = field(default_factory=list)


@dataclass
class BinaryExpr(_Ast):
    left: object
    op: BoolOp
    right: object
    fields: List[str] = field(default_factory=list)


@dataclass
class GroupExpr(_Ast):
    child: object
    fields: List[str] = field(default_factory=list)


@dataclass
class OutputSpecExpr(_Ast):
    target: OutputTarget
    child: object


@dataclass
class Query(_Ast):
    """Root node returned by `Parser.__call__`."""

    body: object
