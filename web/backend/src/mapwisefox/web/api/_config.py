from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from mapwisefox.web._deps import current_user, settings
from mapwisefox.web.config import AppSettings
from mapwisefox.web.model import UserInfo
from .workbooks._cache import SUPPORTED_FIELDS


router = APIRouter(prefix="/api/v1", tags=["configuration"])


class FrontendUser(BaseModel):
    display_name: str
    email: str


class SupportedField(BaseModel):
    name: str
    mandatory: bool


class FrontendConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user: FrontendUser | None
    supported_fields: list[SupportedField] = Field(alias="supportedFields")
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
        supportedFields=[
            SupportedField(name=name, mandatory=mandatory)
            for name, mandatory in SUPPORTED_FIELDS.items()
        ],
        decisionColumn=config.decision_column,
        exclusionReasonColumn=config.exclusion_reason_column,
    )
