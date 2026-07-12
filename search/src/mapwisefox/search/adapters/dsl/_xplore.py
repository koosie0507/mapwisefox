from typing import Any

from mapwisefox.search import (
    EvidenceAttributes,
    AttrExpr,
    EvidenceTypeExpr,
    YearRangeExpr,
    EvidenceTypes,
)
from mapwisefox.search.adapters._flat_output import (
    FlatOutputAdapter,
)


class XploreAdapter(FlatOutputAdapter):
    ATTR_MAP = {
        EvidenceAttributes.TITLE: "Document Title",
        EvidenceAttributes.ABSTRACT: "Abstract",
        EvidenceAttributes.KEYS: "Author Keywords",
    }
    DOCTYPE_MAP = {
        EvidenceTypes.ARTICLE: "Journals",
        EvidenceTypes.CONFERENCE: "Conferences",
    }

    def __init__(self):
        super().__init__()
        self._doc_types = set()
        self._year_range = None

    def _stringify(self, item):
        if isinstance(item, str):
            return item
        is_wildcard = "*" in item.value or "?" in item.value
        value = item.value if is_wildcard else f'"{item.value}"'
        return f'"{self.ATTR_MAP[item.name]}":{value}'

    def _extract_group_str(self, buf, group):
        query_text_clauses = []
        for item in buf:
            if isinstance(item, EvidenceTypeExpr):
                self._doc_types.add(item.value)
            elif (
                isinstance(item, AttrExpr) and item.name in self.ATTR_MAP
            ) or isinstance(item, str):
                query_text_clauses.append(item)
            elif isinstance(item, YearRangeExpr):
                self._year_range = item
        query_text = f" {group.op.upper()} ".join(
            map(self._stringify, query_text_clauses)
        )
        return f"({query_text})" if len(query_text) > 0 else ""

    def result(self):
        params: dict[str, Any] = {
            "query_text": self._output.getvalue(),
        }
        supported_doc_types = [
            self.DOCTYPE_MAP[doc_type]
            for doc_type in self._doc_types
            if doc_type in self.DOCTYPE_MAP
        ]
        if len(supported_doc_types) > 0:
            params["content_type"] = supported_doc_types
        if self._year_range is not None:
            params["start_year"] = self._year_range.start
            params["end_year"] = self._year_range.end
        return params
