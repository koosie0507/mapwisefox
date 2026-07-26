from io import BytesIO

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from openpyxl import Workbook

from mapwisefox.web.api import workbooks_api_router
from mapwisefox.web._deps import current_user, settings, user_upload_dir
from mapwisefox.web.config import AppSettings


HEADERS = [
    "title",
    "abstract",
    "doi",
    "authors",
    "keywords",
    "year",
    "source",
    "url",
    "has_pdf",
    "referencing_paper_ids",
]


@pytest.fixture
def workbook_file():
    stream = BytesIO()
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Studies"
    worksheet.append(HEADERS)
    worksheet.append(
        [
            "Title",
            "Abstract",
            "10.1/test",
            "Ada",
            "test",
            2025,
            "Journal",
            "",
            False,
            "",
        ]
    )
    worksheet.append(
        [
            "Second",
            "Abstract",
            "10.1/second",
            "Grace",
            "test",
            2024,
            "Journal",
            "",
            False,
            "",
        ]
    )
    workbook.save(stream)
    workbook.close()
    return stream.getvalue()


@pytest.fixture
def client(tmp_path):
    app = FastAPI()
    app.include_router(workbooks_api_router)
    config = AppSettings(uploads_dir=tmp_path)
    app.dependency_overrides[current_user] = lambda: None
    app.dependency_overrides[user_upload_dir] = lambda: tmp_path
    app.dependency_overrides[settings] = lambda: config
    return TestClient(app)


@pytest.fixture
def basic_upload(client, workbook_file):
    def _():
        return client.post(
            "/api/v1/workbooks",
            files={"file": ("studies.xlsx", workbook_file)},
            data={"worksheetName": "Studies", "expectedColumns": "title,abstract"},
        )

    return _


@pytest.fixture
def selection_criteria_json():
    return (
        b'{"review_topic":"entity resolution",'
        b'"inclusion_criteria":[{"label":"english","description":"written in English"}],'
        b'"exclusion_criteria":[{"label":"not software","description":"no software"}]}'
    )


@pytest.fixture
def imported_client(client, workbook_file, basic_upload):
    response = basic_upload()
    assert response.status_code == 201
    return client


@pytest.fixture
def async_client(tmp_path):
    app = FastAPI()
    app.include_router(workbooks_api_router)
    app.dependency_overrides[user_upload_dir] = lambda: tmp_path
    app.dependency_overrides[settings] = lambda: AppSettings(uploads_dir=tmp_path)
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
