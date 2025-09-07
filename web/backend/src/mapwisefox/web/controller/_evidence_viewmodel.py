from typing import Optional, Literal
from urllib.parse import urlencode

from pydantic import BaseModel, model_validator, Field

from mapwisefox.web.utils import any_to_bool
from mapwisefox.web.model import Evidence, NavigateAction


class NavigateRequestBody(BaseModel):
    cluster_id: int = Field(..., alias="clusterId")
    action: NavigateAction


class ToggleEvidenceStatusRequestBody(BaseModel):
    cluster_id: int = Field(..., alias="clusterId")
    include: bool
    exclude_reasons: list[str] = Field(..., alias="excludeReasons")


class EvidenceViewModel(Evidence):
    selection_status: Optional[str] = None
    published_at: Optional[str] = Field(None, alias="publishedAt")
    doi_link: Optional[str] = Field(None, alias="doiLink")
    scihub_link: Optional[str] = Field(None, alias="sciHubLink")

    def __init__(self, evidence: Evidence):
        super().__init__(**evidence.model_dump())

    @model_validator(mode="before")
    @classmethod
    def _coerce_values(cls, data: dict) -> dict:
        data = super()._coerce_values(data)
        if data.get("url") is None:
            data["url"] = "https://www.semanticscholar.org/search?{}".format(
                urlencode({
                    "q": data["title"],
                })
            )
        if data.get("publication_date"):
            data["published_at"] = data["publication_date"].strftime("%Y-%m-%d")
        if exclude_reasons:=data.get("exclude_reasons"):
            data["exclude_reasons"] = [
                r.strip()
                for reason_string in exclude_reasons
                for r in reason_string.split(",")
            ]
            data["include"] = len(exclude_reasons) == 0
        else:
            data["include"] = True

        if not data.get("publication_venue"):
            data["publication_venue"] = "<not specified>"
        if data.get("doi"):
            data["doi_link"] = f"https://dx.doi.org/{data["doi"]}"
            data["scihub_link"] = f"https://sci-hub.se/{data["doi"]}"
        data["selection_status"] = "include" if any_to_bool(data["include"]) else "exclude"
        return data

    def serialize_lists(self, data: list, _info):
        return data

    def serialize_include(self, include: bool, _) -> str|bool:
        return include


class NavigateResponseBody(BaseModel):
    evidence: EvidenceViewModel
    min_id: int = Field(..., alias="minId")
    max_id: int = Field(..., alias="maxId")


class ToggleEvidenceStatusResponseBody(BaseModel):
    evidence: EvidenceViewModel
    changed: bool
    complete: bool
