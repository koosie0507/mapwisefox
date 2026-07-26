from typing import Optional
from urllib.parse import urlencode

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mapwisefox.common.config import SelectionConfig
from mapwisefox.web.model import Decision, Evidence
from mapwisefox.web.utils import any_to_bool


class ScreeningPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    decision: Decision
    exclusion_reasons: list[str] = Field(default_factory=list, alias="exclusionReasons")

    @model_validator(mode="after")
    def validate_excluded(self):
        if self.decision == "excluded" and not any(
            reason.strip() for reason in self.exclusion_reasons
        ):
            raise ValueError("Excluded records require at least one exclusion reason")
        return self


class EvidenceResponse(Evidence):
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
                urlencode(
                    {
                        "q": data["title"],
                    }
                )
            )
        if data.get("publication_date"):
            data["published_at"] = data["publication_date"].strftime("%Y-%m-%d")
        if exclude_reasons := data.get("exclude_reasons"):
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
            data_doi = data["doi"]
            data["doi_link"] = f"https://dx.doi.org/{data_doi}"
            data["scihub_link"] = f"https://sci-hub.se/{data_doi}"
        data["selection_status"] = (
            "include" if any_to_bool(data["include"]) else "exclude"
        )
        return data

    def serialize_lists(self, data: list, _info):
        return data

    def serialize_include(self, include: bool, _) -> str | bool:
        return include


class ScreeningResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    record_index: int = Field(alias="recordIndex")
    record_count: int = Field(alias="recordCount")
    decision: Decision
    exclusion_reasons: list[str] = Field(alias="exclusionReasons")
    evidence: EvidenceResponse
    previous_index: int | None = Field(alias="previousIndex")
    next_index: int | None = Field(alias="nextIndex")
    first_undecided_index: int | None = Field(alias="firstUndecidedIndex")
    next_undecided_index: int | None = Field(alias="nextUndecidedIndex")
    complete: bool
    selection_criteria: SelectionConfig | None = Field(
        default=None, alias="selectionCriteria"
    )
