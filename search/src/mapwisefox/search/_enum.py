from enum import StrEnum


class EvidenceAttributes(StrEnum):
    DOCTYPE = "document type"
    TITLE = "title"
    ABSTRACT = "abstract"
    KEYS = "keys"
    SUBJECT = "subject area"
    LANGUAGE = "language"


class EvidenceTypes(StrEnum):
    ARTICLE = "journal"
    CONFERENCE = "proceedings"
    REPORT = "report"


class SubjectAreas(StrEnum):
    COMPUTER_SCIENCE = "compsci"
    ENGINEERING = "eng"
    MATHEMATICS = "math"
