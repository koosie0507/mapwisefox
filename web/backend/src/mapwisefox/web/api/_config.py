from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from mapwisefox.web._deps import current_user, settings
from mapwisefox.web.config import AppSettings
from mapwisefox.web.model import UserInfo


router = APIRouter(prefix="/api/v1", tags=["configuration"])


class FrontendUser(BaseModel):
    display_name: str
    email: str


class FrontendConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user: FrontendUser | None
    worksheet_name: str = Field(alias="worksheetName")
    expected_columns: str = Field(alias="expectedColumns")
    decision_column: str = Field(alias="decisionColumn")
    exclusion_reason_column: str = Field(alias="exclusionReasonColumn")


@router.get("/config", response_model=FrontendConfig, response_model_by_alias=True)
def frontend_config(
    config: AppSettings = Depends(settings),
    user: UserInfo | None = Depends(current_user),
) -> FrontendConfig:
    frontend_user = (
        FrontendUser(display_name=user.display_name, email=user.email) if user else None
    )
    return FrontendConfig(
        user=frontend_user,
        worksheetName=config.worksheet_name or "",
        expectedColumns=config.expected_columns or "",
        decisionColumn=config.decision_column,
        exclusionReasonColumn=config.exclusion_reason_column,
    )
