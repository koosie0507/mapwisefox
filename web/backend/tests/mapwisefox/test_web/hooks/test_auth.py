import json
import time

import asyncio

import pytest
from authlib.jose.errors import ExpiredTokenError
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mapwisefox.web._auth import FileOidcCache, TokenService, user_from_claims
from mapwisefox.web._origin import OriginGuardMiddleware
from mapwisefox.web.config import AppSettings
from mapwisefox.web.hooks import auth_hooks


def test_user_from_claims_uses_issuer_and_subject():
    user = user_from_claims(
        {
            "iss": "https://identity.example.com",
            "sub": "user-123",
            "name": "Ada Lovelace",
            "email": "ada@example.com",
        }
    )

    assert user.dirname == (
        "06ccc2839b883e691e4a9d49627c65d4" "fdcd71ed4a3999afd711d8399587161e"
    )


def test_access_token_round_trips_user():
    service = TokenService("test-secret", "https://api.example.com")
    user = user_from_claims(
        {"iss": "https://identity.example.com", "sub": "123", "name": "Ada"}
    )

    token = service.issue_access_token(user)

    assert service.validate_access_token(token) == user


def test_expired_access_token_is_rejected():
    service = TokenService("test-secret", "https://api.example.com")
    token = service._issue(  # noqa: SLF001 - explicit expiry is the behavior under test
        {
            "sub": "123",
            "identity_issuer": "https://identity.example.com",
            "dirname": "abc",
            "name": "Ada",
            "email": "",
        },
        "access",
        now=int(time.time()) - 120,
        lifetime=1,
    )

    with pytest.raises(ExpiredTokenError):
        service.validate_access_token(token)


def test_oidc_state_survives_cache_recreation(tmp_path):
    path = tmp_path / "oidc.json"
    cache = FileOidcCache(path)
    asyncio.run(cache.set("state", json.dumps({"data": {"nonce": "abc"}}), 60))

    restored = asyncio.run(FileOidcCache(path).get("state"))

    assert json.loads(restored)["data"]["nonce"] == "abc"


@pytest.fixture
def auth_client(tmp_path):
    config = AppSettings(
        auth_enabled=True,
        uploads_dir=tmp_path,
        oidc_discovery_url="https://identity.example.com/.well-known/openid-configuration",
        oidc_client_id="client",
        oidc_client_secret="secret",
        public_url="https://api.example.com",
        allowed_origins="https://app.example.com",
        token_secret="x" * 32,
    )
    app = FastAPI()
    app.state.config = config
    app.state.oidc = object()
    app.state.tokens = TokenService(config.token_secret, config.public_url)
    app.add_middleware(OriginGuardMiddleware, config=config)
    app.include_router(auth_hooks)
    return TestClient(app)


def test_refresh_returns_access_token_for_allowed_origin(auth_client):
    user = user_from_claims(
        {"iss": "https://identity.example.com", "sub": "123", "name": "Ada"}
    )
    auth_client.cookies.set(
        "mwf_refresh", auth_client.app.state.tokens.issue_refresh_token(user)
    )

    response = auth_client.post(
        "/auth/refresh", headers={"Origin": "https://app.example.com"}
    )

    assert response.json()["token_type"] == "Bearer"


def test_refresh_rejects_unapproved_origin(auth_client):
    response = auth_client.post(
        "/auth/refresh", headers={"Origin": "https://attacker.example.com"}
    )

    assert response.status_code == 403
