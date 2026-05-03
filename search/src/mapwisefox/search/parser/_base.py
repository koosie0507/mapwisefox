from abc import ABCMeta, abstractmethod
from functools import singledispatchmethod

from lark import Tree

from ._ir import (
    ValueExpr,
    BinaryExpr,
    GroupExpr,
    UnaryExpr,
    MatchExpr,
    OutputSpecExpr,
    OutputTarget,
)


class DSLAdapter(metaclass=ABCMeta):
    """
    Base adapter: dispatches on IR node type via singledispatchmethod,
    mirroring how ast_utils.create_transformer dispatches on grammar rule
    by class name.

    Subclasses override the typed emit_* methods; they never touch adapt()
    or the dispatch table.
    """

    # ── public entry point ────────────────────────────────────────────────────

    @singledispatchmethod
    def adapt(self, node) -> object:
        raise TypeError(f"No adapter registered for IR node type: {type(node)!r}")

    # ── register one handler per IR node type ─────────────────────────────────

    @adapt.register(ValueExpr)
    def _(self, node: ValueExpr) -> str:
        return self.emit_value(node)

    @adapt.register(BinaryExpr)
    def _(self, node: BinaryExpr) -> str:
        return self.emit_binary(node)

    @adapt.register(UnaryExpr)
    def _(self, node: UnaryExpr) -> str:
        # UnaryExpr wraps either a negation child or a MatchExpr
        if isinstance(node.child, MatchExpr):
            return self.adapt(node.child)
        return self.emit_not(node)

    @adapt.register(MatchExpr)
    def _(self, node: MatchExpr) -> str:
        tag = node.op[0]
        if tag == "approx":
            return self.emit_approx(node)
        elif tag == "nearest":
            return self.emit_nearest(node)
        else:  # "match"
            return self.emit_match(node)

    @adapt.register(GroupExpr)
    def _(self, node: GroupExpr) -> str:
        return self.emit_group(node)

    @adapt.register(OutputSpecExpr)
    def _(self, node: OutputSpecExpr) -> dict:
        return self.emit_output(node)

    # ── abstract: subclasses must implement these ─────────────────────────────

    @abstractmethod
    def emit_value(self, node: ValueExpr) -> str: ...

    @abstractmethod
    def emit_binary(self, node: BinaryExpr) -> str: ...

    @abstractmethod
    def emit_not(self, node: UnaryExpr) -> str: ...

    # ── concrete defaults: subclasses may override ────────────────────────────

    def emit_group(self, node: GroupExpr) -> str:
        return f"({self.adapt(node.child)})"

    def emit_approx(self, node: MatchExpr) -> str:
        """Default: treat approx as a plain grouped expression."""
        return self.adapt(node.child)

    def emit_nearest(self, node: MatchExpr) -> str:
        """Default: treat nearest as a plain grouped expression."""
        return self.adapt(node.child)

    def emit_match(self, node: MatchExpr) -> str:
        """Default: treat match as a plain expression."""
        return self.adapt(node.child)

    def emit_output(self, node: OutputSpecExpr) -> dict:
        """
        Default routing: emit the child and wrap in a dict keyed by target.
        Subclasses can override to split query vs. filter differently.
        """
        child_str = self.adapt(node.child)
        return {
            OutputTarget.QUERY: (
                child_str if node.target != OutputTarget.FILTER else None
            ),
            OutputTarget.FILTER: (
                child_str if node.target != OutputTarget.QUERY else None
            ),
        }
