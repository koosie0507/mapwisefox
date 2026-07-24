from pathlib import Path

from pydantic import Field, DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="mwf_web_")

    auth_enabled: bool = False
    uploads_dir: DirectoryPath = Field(Path.cwd() / "uploads")
    worksheet_name: str | None = None
    expected_columns: str | None = None
    decision_column: str = "include"
    exclusion_reason_column: str = "exclude_reason"
    ms_client_id: str | None = Field(None)
    ms_client_secret: str | None = Field(None)
    ms_tenant_id: str | None = Field(None)
