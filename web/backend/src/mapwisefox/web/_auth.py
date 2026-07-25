import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from authlib.jose import JsonWebToken
from authlib.jose.errors import JoseError
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.responses import RedirectResponse

from mapwisefox.web.config import AppSettings
from mapwisefox.web.model import UserInfo


ACCESS_TOKEN_LIFETIME = 10 * 60
REFRESH_TOKEN_LIFETIME = 30 * 24 * 60 * 60
TOKEN_LEEWAY = 30
TOKEN_AUDIENCE = "mapwisefox-api"
OIDC_CACHE_LIFETIME = 24 * 60 * 60
OIDC_STATE_LIFETIME = 10 * 60
OIDC_SIGNING_ALGORITHMS = {
    "RS256",
    "RS384",
    "RS512",
    "PS256",
    "PS384",
    "PS512",
    "ES256",
    "ES384",
    "ES512",
}


def user_from_claims(claims: dict[str, Any]) -> UserInfo:
    issuer = str(claims["iss"])
    subject = str(claims["sub"])
    identity = hashlib.sha256(f"{issuer}\0{subject}".encode()).hexdigest()
    email = str(claims.get("email") or claims.get("preferred_username") or "")
    display_name = str(claims.get("name") or email or subject)
    return UserInfo(
        dirname=identity,
        issuer=issuer,
        subject=subject,
        display_name=display_name,
        email=email,
    )


class TokenService:
    def __init__(self, secret: str, issuer: str) -> None:
        self._secret = secret
        self._issuer = issuer.rstrip("/")
        self._jwt = JsonWebToken(["HS256"])

    def issue_access_token(self, user: UserInfo) -> str:
        return self._issue(
            self._user_claims(user), "access", lifetime=ACCESS_TOKEN_LIFETIME
        )

    def issue_refresh_token(self, user: UserInfo) -> str:
        return self._issue(
            self._user_claims(user), "refresh", lifetime=REFRESH_TOKEN_LIFETIME
        )

    def validate_access_token(self, token: str) -> UserInfo:
        return self._validate(token, "access")

    def validate_refresh_token(self, token: str) -> UserInfo:
        return self._validate(token, "refresh")

    def _issue(
        self,
        claims: dict[str, Any],
        token_type: str,
        *,
        lifetime: int,
        now: int | None = None,
    ) -> str:
        issued_at = int(time.time()) if now is None else now
        payload = {
            **claims,
            "iss": self._issuer,
            "aud": TOKEN_AUDIENCE,
            "iat": issued_at,
            "nbf": issued_at,
            "exp": issued_at + lifetime,
            "jti": str(uuid4()),
        }
        token = self._jwt.encode(
            {"alg": "HS256", "typ": f"mwf-{token_type}+jwt"}, payload, self._secret
        )
        return token.decode()

    def _validate(self, token: str, token_type: str) -> UserInfo:
        options = {
            name: {"essential": True}
            for name in ("iss", "sub", "aud", "iat", "nbf", "exp", "jti")
        }
        options["iss"]["value"] = self._issuer
        options["aud"]["value"] = TOKEN_AUDIENCE
        options.update(
            {
                name: {"essential": True}
                for name in ("identity_issuer", "dirname", "name")
            }
        )
        claims = self._jwt.decode(token, self._secret, claims_options=options)
        if claims.header.get("typ") != f"mwf-{token_type}+jwt":
            raise JoseError("Invalid token type")
        claims.validate(leeway=TOKEN_LEEWAY)
        return UserInfo(
            dirname=claims["dirname"],
            issuer=claims["identity_issuer"],
            subject=claims["sub"],
            display_name=claims["name"],
            email=claims["email"],
        )

    @staticmethod
    def _user_claims(user: UserInfo) -> dict[str, str]:
        return {
            "sub": user.subject,
            "identity_issuer": user.issuer,
            "dirname": user.dirname,
            "name": user.display_name,
            "email": user.email,
        }


class FileOidcCache:
    _locks: dict[Path, threading.RLock] = {}
    _locks_guard = threading.Lock()

    def __init__(self, path: Path) -> None:
        self._path = path
        with self._locks_guard:
            self._lock = self._locks.setdefault(path.resolve(), threading.RLock())

    async def get(self, key: str) -> str | None:
        with self._lock:
            data = self._read()
            entry = data["states"].get(key)
            if not entry or entry["expires_at"] < time.time():
                return None
            return entry["value"]

    async def set(self, key: str, value: str, expires_in: int) -> None:
        with self._lock:
            data = self._read()
            data["states"][key] = {
                "value": value,
                "expires_at": time.time() + expires_in,
            }
            self._write(data)

    async def delete(self, key: str) -> None:
        with self._lock:
            data = self._read()
            data["states"].pop(key, None)
            self._write(data)

    def metadata(self) -> dict[str, Any] | None:
        with self._lock:
            return self._read().get("metadata")

    def store_metadata(self, metadata: dict[str, Any]) -> None:
        with self._lock:
            data = self._read()
            data["metadata"] = metadata
            self._write(data)

    def _read(self) -> dict[str, Any]:
        if not self._path.exists():
            return {"states": {}, "metadata": None}
        try:
            data = json.loads(self._path.read_text())
        except (OSError, ValueError):
            return {"states": {}, "metadata": None}
        data.setdefault("states", {})
        data.setdefault("metadata", None)
        now = time.time()
        data["states"] = {
            key: value
            for key, value in data["states"].items()
            if value["expires_at"] >= now
        }
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_suffix(f"{self._path.suffix}.tmp")
        temporary.write_text(json.dumps(data, separators=(",", ":")))
        os.chmod(temporary, 0o600)
        os.replace(temporary, self._path)


class OidcService:
    def __init__(self, config: AppSettings) -> None:
        self._config = config
        self.cache = FileOidcCache(config.resolved_oidc_cache_path)
        oauth = OAuth(cache=self.cache)
        self.client = oauth.register(
            name="oidc",
            client_id=config.oidc_client_id,
            client_secret=config.oidc_client_secret,
            server_metadata_url=config.oidc_discovery_url,
            client_kwargs={
                "scope": "openid profile email",
                "code_challenge_method": "S256",
            },
        )
        self.client.framework.expires_in = OIDC_STATE_LIFETIME

    async def begin_login(
        self, request: Request, return_to: str
    ) -> tuple[RedirectResponse, str]:
        await self._prepare_metadata()
        redirect_uri = f"{self._config.public_url.rstrip('/')}/auth/callback"
        response = await self.client.authorize_redirect(request, redirect_uri)
        state = parse_qs(urlsplit(response.headers["location"]).query)["state"][0]
        await self.cache.set(f"return_to:{state}", return_to, OIDC_STATE_LIFETIME)
        return response, state

    async def complete_login(self, request: Request) -> tuple[UserInfo, str]:
        await self._prepare_metadata()
        state = request.query_params.get("state", "")
        return_to = await self.cache.get(f"return_to:{state}")
        token = await self.client.authorize_access_token(request, leeway=TOKEN_LEEWAY)
        await self.cache.delete(f"return_to:{state}")
        self._store_metadata()
        return (
            user_from_claims(dict(token["userinfo"])),
            return_to or self._config.public_url,
        )

    async def _prepare_metadata(self) -> None:
        cached = self.cache.metadata()
        if cached and time.time() - cached["fetched_at"] < OIDC_CACHE_LIFETIME:
            self.client.server_metadata.update(cached["value"])
            self._validate_metadata()
            return
        self.client.server_metadata.clear()
        await self.client.load_server_metadata()
        await self.client.fetch_jwk_set()
        self._validate_metadata()
        self._store_metadata()

    def _store_metadata(self) -> None:
        self.cache.store_metadata(
            {"fetched_at": time.time(), "value": dict(self.client.server_metadata)}
        )

    def _validate_metadata(self) -> None:
        metadata = self.client.server_metadata
        required_urls = (
            "issuer",
            "authorization_endpoint",
            "token_endpoint",
            "jwks_uri",
        )
        if any(not metadata.get(name) for name in required_urls):
            raise RuntimeError("OIDC discovery metadata is incomplete")
        if any(urlsplit(metadata[name]).scheme != "https" for name in required_urls):
            raise RuntimeError("OIDC discovery endpoints must use HTTPS")
        algorithms = (
            set(metadata.get("id_token_signing_alg_values_supported") or ["RS256"])
            & OIDC_SIGNING_ALGORITHMS
        )
        if not algorithms:
            raise RuntimeError("OIDC provider has no supported signing algorithm")
        metadata["id_token_signing_alg_values_supported"] = sorted(algorithms)
