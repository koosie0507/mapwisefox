from pydantic import BaseModel, Field


class QueryObject(BaseModel):
    query: str = ""
    regex: str = ""
    filters: dict[str, object] = Field(default_factory=dict)
