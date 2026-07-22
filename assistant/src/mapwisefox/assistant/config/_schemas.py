from typing import Optional, Literal

from pydantic import BaseModel, Field, field_validator


class SelectionConfig(BaseModel):
    review_topic: str
    additional_context: Optional[str] = None
    inclusion_criteria: list[str] = Field(min_length=1)
    exclusion_criteria: list[str] = Field(min_length=1)


class SelectionResponse(BaseModel):
    answer: Literal["include", "exclude"]
    justification: Optional[str] = None


class QACriterion(BaseModel):
    label: str
    category: str
    question: str
    description: str
    scoring: str


class QAConfig(BaseModel):
    topic: str
    criteria: list[QACriterion] = Field(min_length=1)

    @field_validator("criteria")
    @classmethod
    def _unique_labels(cls, criteria: list[QACriterion]) -> list[QACriterion]:
        labels = [c.label for c in criteria]
        if len(labels) != len(set(labels)):
            raise ValueError(f"criterion labels must be unique, got {labels}")
        return criteria
