import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mapwisefox.web.api import auth_api_router, config_api_router
from mapwisefox.web._deps import current_user, settings, user_upload_dir
from mapwisefox.web.config import AppSettings
from mapwisefox.web.model import UserInfo


@pytest.fixture
def client(tmp_path):
    app = FastAPI()
    app.include_router(auth_api_router)
    app.include_router(config_api_router)
    config = AppSettings(uploads_dir=tmp_path, auth_enabled=False)
    app.dependency_overrides[current_user] = lambda: None
    app.dependency_overrides[user_upload_dir] = lambda: tmp_path
    app.dependency_overrides[settings] = lambda: config
    return TestClient(app)


def test_auth_required_reports_server_configuration(client):
    response = client.get("/api/v1/auth/required")

    assert response.json() == {"required": False}


def test_auth_required_reports_enabled_configuration(client):
    config = client.app.dependency_overrides[settings]().model_copy(
        update={"auth_enabled": True}
    )
    client.app.dependency_overrides[settings] = lambda: config

    response = client.get("/api/v1/auth/required")

    assert response.json() == {"required": True}


def test_config_returns_frontend_context(client):
    response = client.get("/api/v1/config")

    assert response.json() == {
        "user": None,
        "supportedFields": [
            {"name": "title", "mandatory": True},
            {"name": "authors", "mandatory": True},
            {"name": "doi", "mandatory": False},
            {"name": "abstract", "mandatory": False},
            {"name": "keywords", "mandatory": False},
            {"name": "publicationDate", "mandatory": False},
            {"name": "publicationVenue", "mandatory": False},
            {"name": "url", "mandatory": False},
            {"name": "hasPdf", "mandatory": False},
            {"name": "pdfUrl", "mandatory": False},
            {"name": "referencingEvidence", "mandatory": False},
        ],
        "decisionColumn": "include",
        "exclusionReasonColumn": "exclude_reason",
    }


def test_config_returns_current_user(client):
    client.app.dependency_overrides[current_user] = lambda: UserInfo(
        dirname="ada-lovelace",
        issuer="https://identity.example.com",
        subject="ada",
        display_name="Ada Lovelace",
        email="ada@example.com",
    )

    response = client.get("/api/v1/config")

    assert response.json()["user"] == {
        "display_name": "Ada Lovelace",
        "email": "ada@example.com",
    }
