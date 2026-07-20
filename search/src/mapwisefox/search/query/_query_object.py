from pydantic import BaseModel, Field


class QueryObject(BaseModel):
    query: str = ""
    regex: dict[str, str] = Field(default_factory=dict)
    filters: dict[str, list[str]] = Field(default_factory=dict)
