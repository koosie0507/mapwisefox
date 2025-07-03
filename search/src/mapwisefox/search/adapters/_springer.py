from datetime import datetime, timezone


from mapwisefox.search import (
    EvidenceAttributes,
    EvidenceTypes,
    EvidenceTypeExpr,
    YearRangeExpr,
    SubjectAreaExpr,
    TitleExpr,
)
from mapwisefox.search._expr import (
    NaryExpr,
    AttrExpr,
    LanguageExpr,
    LogicalOperators,
)
from mapwisefox.search.adapters._expr_tree import ExprTreeAdapter


class SpringerAdapter(ExprTreeAdapter):
    ATTR_MAP = {
        EvidenceAttributes.TITLE: "title",
        EvidenceAttributes.ABSTRACT: "Abstract",
        EvidenceAttributes.KEYS: "keyword",
        EvidenceAttributes.LANGUAGE: "language",  # only premium
        EvidenceAttributes.SUBJECT: "subject",  # only premium
        EvidenceAttributes.DOCTYPE: "type",
    }
    DOC_TYPES = {
        EvidenceTypes.ARTICLE: "Journal",
    }

    def __init__(self, is_premium=False):
        super().__init__()
        self._is_premium = is_premium

    def _emit_expr(self, expr):
        if isinstance(expr, EvidenceTypeExpr):
            doc_type = self.DOC_TYPES.get(expr.value)
            return f'"{doc_type}"' if doc_type else None
        if isinstance(expr, YearRangeExpr):
            return f"datefrom:{expr.start:04}-01-01 AND dateto:{expr.end:04}-{datetime.now(timezone.utc).month:02}-01"
        if isinstance(expr, LanguageExpr):
            if not self._is_premium:
                return None
            return '"English"'
        if isinstance(expr, SubjectAreaExpr):
            if not self._is_premium:
                return None
            return '"Computer Science"'
        if isinstance(expr, AttrExpr):
            attr_value = expr.value.replace("?", "+")
            attr_value = {
                "tool*": "tooling",
                "architect*": "architecture",
            }.get(attr_value, attr_value)
            include_attr = (
                expr.name in {EvidenceAttributes.KEYS, EvidenceAttributes.TITLE}
                if self._is_premium
                else expr.name == EvidenceAttributes.KEYS
            )
            if include_attr:
                return f'{self.ATTR_MAP[expr.name]}:"{attr_value}"'
            return f'"{attr_value}"'
        return super()._emit_expr(expr)

    def _get_all_keyword_exprs(self):
        queue = [self._root]
        while queue:
            node = queue.pop(0)
            if isinstance(node, AttrExpr) and node.name == EvidenceAttributes.KEYS:
                yield node
            if isinstance(node, NaryExpr):
                for child in node.children:
                    queue.append(child)

    def _should_include_attr(self, attr_name):
        if attr_name in {EvidenceAttributes.SUBJECT, EvidenceAttributes.LANGUAGE}:
            return self._is_premium
        return attr_name in self.ATTR_MAP

    def _build_regex(self, expr_dict):
        s = [expr_dict[EvidenceAttributes.TITLE]]
        stack = []
        while s:
            node = s.pop()
            if isinstance(node, TitleExpr):
                stack[-1].append(node)
            elif isinstance(node, NaryExpr):
                stack.append([node.op])
                relevant_children = [
                    child
                    for child in node.children
                    if isinstance(child, (TitleExpr, NaryExpr))
                ]
                for child in relevant_children:
                    s.append(child)
        carry = []
        regex_op = ""
        while len(stack) > 0:
            current_level = stack.pop()
            regex_op = (
                current_level[0]
                .replace(LogicalOperators.AND, ".+")
                .replace(LogicalOperators.OR, "|")
            )

            def value_regex(expr):
                return expr.value.replace("?", ".").replace("*", ".*")

            current_level_values = [
                value_regex(c) for c in current_level if isinstance(c, TitleExpr)
            ]
            carry = [c for c in current_level[1:] if isinstance(c, str)]
            if len(current_level_values) > 0:
                carry.append(f"({regex_op.join(current_level_values)})")
            if len(stack) > 0:
                stack[-1].extend(carry)
        final = regex_op.join(carry)
        return final

    def _emit_factored(self, root_op, expr_dict):
        disjunctive_attrs = {EvidenceAttributes.TITLE, EvidenceAttributes.ABSTRACT}
        basic_clauses = [
            f"{f'{self.ATTR_MAP[key]}:' if key != EvidenceAttributes.KEYS else ""}{self._emit_expr(expr)}"
            for key, expr in expr_dict.items()
            if self._should_include_attr(key) and key not in disjunctive_attrs
        ]
        top_level_clauses = [
            # self._emit_expr(expr_dict[EvidenceAttributes.TITLE]),
            *basic_clauses,
        ]
        pub_range = expr_dict.get(self.YEAR_RANGE_KEY)
        if pub_range:
            top_level_clauses.append(self._emit_expr(pub_range))

        return {
            "query": f" {root_op.upper()} ".join(top_level_clauses),
            "regex": self._build_regex(expr_dict),
        }
