from datetime import datetime, UTC
from typing import Any, Optional

import arrow
import numpy as np
from pydantic import BaseModel, model_validator


NON_VALUES = {
    None,
    "",
    "\r",
    "\n",
    "\t",
    " ",
    "nan",
    np.nan,
}


class Evidence(BaseModel):
    cluster_id: int
    include: bool
    doi: str
    title: str
    abstract: str
    authors: list[str]
    keywords: list[str]
    publication_date: Optional[datetime]
    publication_venue: str
    url: str
    has_pdf: bool
    pdf_url: str
    exclude_reasons: list[str]
    referencing_evidence: list[str]

    @staticmethod
    def _parse_list(data: dict[str, Any], field: str, separator: str = ";") -> list[str]:
        if data.get(field) is None:
            return []
        if isinstance(data[field], (list, tuple, set, dict)):
            return list(x for x in data[field])
        if not isinstance(data[field], str):
            data[field] = str(data[field])
        return [
            x.strip()
            for x in data[field].split(separator)
            if x is not None and len(x.strip()) > 0
        ]

    @staticmethod
    def _parse_date(data: dict[str, Any], field: str) -> datetime | None:
        if field not in data or data[field] is None:
            return None
        if not isinstance(data[field], str):
            pubdate_str = str(data[field])
        else:
            pubdate_str = data[field]
        if pubdate_str in NON_VALUES:
            return None
        try:
            if pubdate_str.isdigit():
                return datetime(year=int(pubdate_str), month=1, day=1, tzinfo=UTC)
            else:
                return arrow.get(pubdate_str).to("UTC").datetime

        except ValueError as e:
            raise ValueError(f"Invalid publication date: '{pubdate_str}'") from e

    @staticmethod
    def _parse_boolean(data: dict[str, Any], field: str) -> Any:
        if data.get(field) in NON_VALUES:
            return False
        bool_str = str(data[field]).lower()
        if bool_str == "include":
            return True
        if bool_str == "exclude":
            return False
        # pydantic already handles more common str -> bool conversions
        return bool_str

    @model_validator(mode="before")
    @classmethod
    def _coerce_values(cls, data: dict[str, Any]) -> "dict[str, Any] | Evidence":
        if isinstance(data, cls):
            return data
        for field in ["authors", "keywords", "exclude_reasons", "referencing_evidence"]:
            data[field] = cls._parse_list(data, field)
        for field in ["include", "has_pdf"]:
            data[field] = cls._parse_boolean(data, field)
        data["publication_date"] = cls._parse_date(data, "publication_date")
        return data
