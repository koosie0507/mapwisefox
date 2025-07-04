from pathlib import Path

from pydantic import Field, DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='mwf_web_')

    auth_enabled: bool = False
    basedir: DirectoryPath = Field(Path(__file__).parent)
    uploads_dir: DirectoryPath = Field(Path.cwd() / "uploads")
    ms_client_id: str | None = Field(None)
    ms_client_secret: str | None = Field(None)
    ms_tenant_id: str | None = Field(None)
