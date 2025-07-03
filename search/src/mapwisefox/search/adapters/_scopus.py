from mapwisefox.search._enum import (
    EvidenceAttributes,
    EvidenceTypes,
    SubjectAreas,
)
from mapwisefox.search.adapters._flat_output import (
    FlatOutputAdapter,
)
from mapwisefox.search._expr import (
    AttrExpr,
    YearRangeExpr,
    EvidenceTypeExpr,
    SubjectAreaExpr,
    LanguageExpr,
    AuthorKeysExpr,
)


class ScopusAdapter(FlatOutputAdapter):
    EVIDENCE_TYPES_MAP = {
        EvidenceTypes.ARTICLE: "ar",
        EvidenceTypes.CONFERENCE: "cp",
        EvidenceTypes.REPORT: "rp",
    }
    SUBJECT_AREAS_MAP = {
        SubjectAreas.COMPUTER_SCIENCE: "COMP",
    }

    @staticmethod
    def _extract_mapped_value(value_map, prefix, value):
        value = value_map.get(value, value)
        return f'{prefix}("{value}")'

    @staticmethod
    def _stringify(item):
        if isinstance(item, YearRangeExpr):
            return f"(PUBYEAR AFT {item.start-1} AND PUBYEAR BEF {item.end+1})"
        if isinstance(item, EvidenceTypeExpr):
            return ScopusAdapter._extract_mapped_value(
                ScopusAdapter.EVIDENCE_TYPES_MAP, "DOCTYPE", item.value
            )
        if isinstance(item, SubjectAreaExpr):
            return ScopusAdapter._extract_mapped_value(
                ScopusAdapter.SUBJECT_AREAS_MAP, "SUBJAREA", item.value
            )
        if isinstance(item, LanguageExpr):
            return f'LANGUAGE("{item.value}")'
        if isinstance(item, AuthorKeysExpr):
            return f'AUTHKEY("{item.value}")'

        return str(item)

    def _extract_group_str(self, buf, group):
        if all(isinstance(c, AttrExpr) for c in buf):
            values = {c.value for c in buf}
            fields = {c.name for c in buf}
            prefix = ""
            if (
                EvidenceAttributes.TITLE in fields
                and EvidenceAttributes.ABSTRACT in fields
            ):
                prefix = "TITLE-ABS"
            if len(values) == 1 and len(prefix) > 0:
                return f'{prefix}("{next(iter(values))}")'

        # fallback
        joined = f" {group.op.upper()} ".join(self._stringify(c) for c in buf)
        return f"({joined})"
