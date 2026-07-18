# Intermediate representation (IR)

The IR is a tree of plain dataclasses defined in `mapwisefox.search.dsl.parser._ir`.
Every node subclasses `_Ast` (or `_AstWithMeta` when source position metadata is
needed), which is how `lark.ast_utils.create_transformer` auto-discovers them.

Nodes that can carry a DSL `in <fields>` clause expose a `fields: list[str]`
attribute, populated by the `compound_expr` handling in `_parser.py` — the
grammar's `attr_clause` rule is fully consumed by the transformer and never
appears in the final tree (`AttrClause` should never leak into IR you're
working with).

::: mapwisefox.search.dsl.parser._ir
    options:
      show_root_heading: false
      members:
        - BoolOp
        - MatchType
        - OutputTarget
        - FieldList
        - MatchOp
        - ValueExpr
        - MatchExpr
        - DateExpr
        - UnaryExpr
        - BinaryExpr
        - GroupExpr
        - OutputSpecExpr
        - Query
