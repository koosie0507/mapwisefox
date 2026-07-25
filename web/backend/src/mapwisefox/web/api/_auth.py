from fastapi import APIRouter, Depends
from pydantic import BaseModel

from mapwisefox.web._deps import settings
from mapwisefox.web.config import AppSettings


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


class AuthenticationRequirement(BaseModel):
    required: bool


@router.get("/required", response_model=AuthenticationRequirement)
def authentication_required(
    config: AppSettings = Depends(settings),
) -> AuthenticationRequirement:
    return AuthenticationRequirement(required=config.auth_enabled)
