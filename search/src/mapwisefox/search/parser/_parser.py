from pathlib import Path

from lark import Lark, Transformer, ast_utils, v_args

from ._ir import (
    this_module,
    AttrClause,
    BoolOp,
    MatchType,
    OutputTarget,
    # needed so AsList works correctly
)


class ToAst(Transformer):
    """
    Handles terminals and rules that don't map 1-to-1 to an _Ast dataclass.
    create_transformer() delegates everything else automatically.
    """

    def STRING(self, tok):
        return str(tok)[1:-1]  # strip surrounding quotes

    def CNAME(self, tok):
        return str(tok)

    def SIGNED_NUMBER(self, tok):
        return int(tok)

    def field_name(self, children):
        return children[0]  # already a str from CNAME

    def boolean_op(self, children):
        # children[0] is a Token for "&" or "|"
        # We must NOT use @v_args(inline=True) here — anonymous terminals
        # are kept as Token objects in the children list when keep_all_tokens
        # is False, but the Token itself is still present as children[0].
        if len(children) > 0:
            return BoolOp(str(children[0]))
        return children

    def match_type(self, children):
        return MatchType(str(children[0]))

    def output_spec(self, children):
        # children[0] is the "query"/"filter"/"both" Token
        return OutputTarget(str(children[0]))

    def match_op(self, children):
        # children[0] is always a Token for the keyword
        tag = str(children[0])
        if tag == "approx":
            return ("approx",)
        elif tag == "nearest":
            return ("nearest", children[1])  # int from SIGNED_NUMBER
        else:  # "match"
            return ("match", children[1])  # MatchType

    def compound_expr(self, children):
        node = children[0]
        if len(children) == 2 and isinstance(children[1], AttrClause):
            attr = children[1]
            if hasattr(node, "fields"):
                node.fields = list(attr.field_list.items)
        return node

    @v_args(inline=True)
    def start(self, node):
        return node

    # ── attr_clause attachment ────────────────────────────────────────────────
    # ?compound_expr is transparent, so attr_clause arrives as an extra child
    # on whichever concrete rule (binary_expr, value_expr, etc.) was matched.
    # We post-process by overriding the relevant rules here.
    #
    # Strategy: create_transformer builds the dataclass first, then we check
    # whether the last child was an AttrClause and splice its fields in.

    def _attach_fields(self, node, children):
        # The dataclass was already built by create_transformer; we receive
        # the *raw* children list here only if we define the method ourselves.
        # So we handle this in a post-pass instead (see _attach_attr below).
        return node

    # ── post-pass: attach attr_clause fields to nodes ─────────────────────────
    # Because ?compound_expr is inlined, Lark appends the AttrClause as an
    # extra child to the *parent* rule. We handle this cleanly with a
    # __default__ override that strips AttrClause children and sets .fields.

    def __default__(self, data, children, meta):
        # Separate AttrClause from real children
        attr = None
        real = []
        for c in children:
            if isinstance(c, AttrClause):
                attr = c
            else:
                real.append(c)

        # Let create_transformer build the node normally (via super)
        node = super().__default__(data, real, meta)

        # Attach fields if present and the node supports it
        if attr is not None and hasattr(node, "fields"):
            node.fields = list(attr.field_list)  # FieldList is AsList → list
        return node


class Parser(object):
    def __init__(self):
        self.__parser = Lark(
            self.__grammar_text(), parser="earley", ambiguity="resolve"
        )
        self.__transformer = ast_utils.create_transformer(
            this_module,
            ToAst(),  # companion for terminals + awkward rules
        )

    @staticmethod
    def __grammar_text() -> str:
        with open(Path(__file__).parent / "grammar.lark", "r") as f:
            return f.read()

    def __call__(self, dsl_text: str) -> "DSLNode":
        tree = self.__parser.parse(dsl_text)
        return self.__transformer.transform(tree)


parse = Parser()
