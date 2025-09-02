from datetime import datetime, UTC
from numbers import Number
from typing import Any, Optional, ClassVar

import arrow
import numpy as np
import pandas as pd
from pydantic import BaseModel, model_validator, model_serializer, field_serializer, Field

from mapwisefox.web.utils import any_to_bool

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
    __LIST_VALUED_FIELDS: ClassVar[list[str]] = ["authors", "keywords", "exclude_reasons", "referencing_evidence"]
    __DEFAULT_LIST_SEPARATOR: ClassVar[str] = ";"

    class Config:
        populate_by_name = True

    cluster_id: int = Field(..., alias="clusterId")
    include: bool
    doi: str
    title: str
    abstract: Optional[str]
    authors: list[str]
    keywords: list[str]
    publication_date: Optional[datetime] = Field(..., alias="publicationDate")
    publication_venue: Optional[str] = Field(..., alias="publicationVenue")
    url: str
    has_pdf: bool = Field(..., alias="hasPdf")
    exclude_reasons: list[str] = Field(..., alias="excludeReasons")
    referencing_evidence: list[str] = Field(..., alias="referencingEvidence")
    pdf_url: Optional[str] = Field(None, alias="pdfUrl")

    @staticmethod
    def _parse_list(data: dict[str, Any], field: str, separator: str = __DEFAULT_LIST_SEPARATOR) -> list[str]:
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
                return datetime(year=int(pubdate_str), month=1, day=1)
            else:
                return arrow.get(pubdate_str).datetime.replace(tzinfo=None)

        except ValueError as e:
            raise ValueError(f"Invalid publication date: '{pubdate_str}'") from e

    @staticmethod
    def _parse_boolean(data: dict[str, Any], field: str) -> Any:
        if data.get(field) in NON_VALUES:
            return False
        return any_to_bool(data[field])

    @model_validator(mode="before")
    @classmethod
    def _coerce_values(cls, data: dict[str, Any]) -> "dict[str, Any] | Evidence":
        if isinstance(data, cls):
            return data
        for field in Evidence.__LIST_VALUED_FIELDS:
            data[field] = cls._parse_list(data, field)
        for field in ["include", "has_pdf"]:
            data[field] = cls._parse_boolean(data, field)
        if (exclude_reasons:=data.get("exclude_reasons")) is None or len(exclude_reasons) == 0:
            data["include"] = True
        for field in data:
            if isinstance(data.get(field), Number) and (pd.isna(data[field]) or np.isnan(data[field])):
                data[field] = None
        data["publication_date"] = cls._parse_date(data, "publication_date")
        return data

    @field_serializer(*__LIST_VALUED_FIELDS)
    def serialize_lists(self, data: list, _info):
        return self.__DEFAULT_LIST_SEPARATOR.join(data)

    @field_serializer("include")
    def serialize_include(self, include: bool, _) -> str:
        return "include" if include else "exclude"

    @field_serializer("publication_date")
    def serialize_publication_date(self, pubdate: datetime, _) -> str:
        return pubdate.isoformat()
