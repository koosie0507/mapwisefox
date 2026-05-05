from abc import ABCMeta, abstractmethod
from functools import singledispatchmethod
from typing import Any

from ._ir import (
    BinaryExpr,
    GroupExpr,
    MatchExpr,
    OutputSpecExpr,
    OutputTarget,
    Query,
    UnaryExpr,
    ValueExpr,
)


class DSLAdapter(metaclass=ABCMeta):

    @singledispatchmethod
    def adapt(self, node: Any) -> Any:
        raise TypeError(f"No adapter registered for IR node type: {type(node)!r}")

    @adapt.register(Query)
    def _(self, node: Query) -> Any:
        return self.emit_query(node)

    @adapt.register(ValueExpr)
    def _(self, node: ValueExpr) -> Any:
        return self.emit_value(node)

    @adapt.register(BinaryExpr)
    def _(self, node: BinaryExpr) -> Any:
        return self.emit_binary(node)

    @adapt.register(UnaryExpr)
    def _(self, node: UnaryExpr) -> Any:
        return self.emit_not(node)

    @adapt.register(MatchExpr)
    def _(self, node: MatchExpr) -> Any:
        tag = node.op.kind
        if tag == "approx":
            return self.emit_approx(node)
        elif tag == "nearest":
            return self.emit_nearest(node)
        else:
            return self.emit_match(node)

    @adapt.register(GroupExpr)
    def _(self, node: GroupExpr) -> Any:
        return self.emit_group(node)

    @adapt.register(OutputSpecExpr)
    def _(self, node: OutputSpecExpr) -> Any:
        return self.emit_output(node)

    @abstractmethod
    def emit_value(self, node: ValueExpr) -> Any: ...

    @abstractmethod
    def emit_binary(self, node: BinaryExpr) -> Any: ...

    @abstractmethod
    def emit_not(self, node: UnaryExpr) -> Any: ...

    def emit_query(self, node: Query) -> Any:
        return self.adapt(node.body)

    def emit_group(self, node: GroupExpr) -> Any:
        return f"({self.adapt(node.child)})"

    def emit_approx(self, node: MatchExpr) -> Any:
        return self.adapt(node.child)

    def emit_nearest(self, node: MatchExpr) -> Any:
        return self.adapt(node.child)

    def emit_match(self, node: MatchExpr) -> Any:
        return self.adapt(node.child)

    def emit_output(self, node: OutputSpecExpr) -> Any:
        child_val = self.adapt(node.child)
        return {
            OutputTarget.QUERY: (
                child_val if node.target != OutputTarget.FILTER else None
            ),
            OutputTarget.FILTER: (
                child_val if node.target != OutputTarget.QUERY else None
            ),
        }
