from pathlib import Path
from urllib.parse import urlsplit

from pydantic import DirectoryPath, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="mwf_web_")

    auth_enabled: bool = False
    uploads_dir: DirectoryPath = Field(Path.cwd() / "uploads")
    decision_column: str = "include"
    exclusion_reason_column: str = "exclude_reason"
    oidc_discovery_url: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    public_url: str | None = None
    allowed_origins: str = ""
    token_secret: str | None = None
    oidc_cache_path: Path | None = None

    @model_validator(mode="after")
    def validate_auth_settings(self):
        if not self.auth_enabled:
            return self
        required = {
            "oidc_discovery_url": self.oidc_discovery_url,
            "oidc_client_id": self.oidc_client_id,
            "oidc_client_secret": self.oidc_client_secret,
            "public_url": self.public_url,
            "token_secret": self.token_secret,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing authentication settings: {', '.join(missing)}")
        if len(self.token_secret or "") < 32:
            raise ValueError("token_secret must contain at least 32 characters")
        public_url = urlsplit(self.public_url or "")
        if public_url.path.rstrip("/") or public_url.query or public_url.fragment:
            raise ValueError("public_url must be an origin without a path")
        if public_url.scheme != "https" and public_url.hostname not in {
            "localhost",
            "127.0.0.1",
        }:
            raise ValueError("public_url must use HTTPS outside local development")
        discovery = urlsplit(self.oidc_discovery_url or "")
        if discovery.scheme != "https" and discovery.hostname not in {
            "localhost",
            "127.0.0.1",
        }:
            raise ValueError("oidc_discovery_url must use HTTPS")
        for origin in self.configured_origins:
            parsed = urlsplit(origin)
            if parsed.scheme != "https" and parsed.hostname not in {
                "localhost",
                "127.0.0.1",
            }:
                raise ValueError("Production allowed origins must use HTTPS")
        return self

    @property
    def resolved_oidc_cache_path(self) -> Path:
        return self.oidc_cache_path or self.uploads_dir / ".oidc-cache.json"

    @property
    def configured_origins(self) -> set[str]:
        return {
            origin.strip().rstrip("/")
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        }
