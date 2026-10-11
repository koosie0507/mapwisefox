import pytest


CANONICAL_CSV = (
    b"title,abstract,doi,authors,keywords,year,source,url\n"
    b"Title One,Abstract One,10.1/one,Aida,tests,2025,Journal,http://one\n"
    b"Second Title,Abstract Two,10.1/two,Grace,tests,2024,Journal,http://two\n"
)

BOM_CANONICAL_CSV = b"\xef\xbb\xbf" + CANONICAL_CSV

WOS_CSV = (
    b"Author Full Names,Article Title,Source Title,Abstract,"
    b"Author Keywords,Publication Year,DOI,DOI Link\n"
    b"John Doe,Test Title,Test Source,Test Abstract,Key1;Key2,"
    b"2023,10.1000/1,http://doi.org/1"
)


@pytest.fixture
def csv_file():
    return CANONICAL_CSV


def test_import_csv_serves_xlsx_resource(client, csv_file):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("studies.csv", csv_file)},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "studies.xlsx"
    assert response.json()["worksheetName"] == "Sheet"
    assert response.json()["recordCount"] == 2
    assert response.json()["unfilledRecordCount"] == 2
    assert response.headers["location"] == "/api/v1/workbooks/studies.xlsx"

    listed = client.get("/api/v1/workbooks").json()
    assert listed[0]["name"] == "studies.xlsx"

    screening = client.get("/api/v1/workbooks/studies.xlsx/screening/0").json()
    assert screening["evidence"]["title"] == "Title One"
    assert screening["evidence"]["authors"] == ["Aida"]
    assert screening["evidence"]["publishedAt"] == "2025-01-01"
    assert screening["evidence"]["publicationVenue"] == "Journal"
    assert screening["evidence"]["doiLink"] == "https://dx.doi.org/10.1/one"
    assert screening["decision"] == "undecided"


def test_import_csv_resolves_provider_columns(client):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("wos_export.csv", WOS_CSV)},
    )

    assert response.status_code == 201
    mapping = response.json()["fieldMappings"]
    assert mapping["title"] == "Article Title"
    assert mapping["authors"] == "Author Full Names"
    assert mapping["publicationDate"] == "Publication Year"

    screening = client.get("/api/v1/workbooks/wos_export.xlsx/screening/0").json()
    assert screening["evidence"]["title"] == "Test Title"
    assert screening["evidence"]["publicationVenue"] == "Test Source"
    assert screening["evidence"]["publishedAt"] == "2023-01-01"
    assert screening["evidence"]["doiLink"] == "https://dx.doi.org/10.1000/1"


def test_import_csv_tolerates_byte_order_mark(client):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("bom.csv", BOM_CANONICAL_CSV)},
    )

    assert response.status_code == 201
    assert response.json()["recordCount"] == 2


def test_import_csv_ignores_worksheet_name(client, csv_file):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("studies.csv", csv_file)},
        data={"worksheetName": "Studies"},
    )

    assert response.status_code == 201
    assert response.json()["worksheetName"] == "Sheet"


def test_import_csv_keeps_explicit_field_mappings(client):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("custom.csv", b"My Title,My Authors\nT1,A1\n")},
        data={"fieldMappings": '{"title":"My Title","authors":"My Authors"}'},
    )

    assert response.status_code == 201
    assert response.json()["fieldMappings"] == {
        "title": "My Title",
        "authors": "My Authors",
    }
    screening = client.get("/api/v1/workbooks/custom.xlsx/screening/0").json()
    assert screening["evidence"]["title"] == "T1"


def test_import_csv_persists_selection_criteria(
    client, csv_file, selection_criteria_json
):
    response = client.post(
        "/api/v1/workbooks",
        files={
            "file": ("studies.csv", csv_file),
            "selectionCriteria": ("criteria.json", selection_criteria_json),
        },
    )

    assert response.status_code == 201
    screening = client.get("/api/v1/workbooks/studies.xlsx/screening/0").json()
    assert screening["selectionCriteria"]["review_topic"] == "entity resolution"


def test_import_rejects_empty_csv(client):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("empty.csv", b"")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "missing_header"
    assert "message" in response.json()["detail"]


def test_import_rejects_duplicate_csv_headers(client):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("dup.csv", b"title,authors,title\nT1,A1,T2\n")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "duplicate_header"
    assert "message" in response.json()["detail"]


def test_import_rejects_blank_csv_headers(client):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("blank.csv", b"title,,authors\nT1,,A1\n")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_header"
    assert "message" in response.json()["detail"]


def test_import_rejects_header_only_csv(client):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("nothing.csv", b"title,authors\n")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "missing_records"


def test_import_rejects_undecodable_csv(client):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("binary.csv", b"\xff\xfe\x00binary")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_workbook"


def test_import_rejects_unsafe_csv_name(client, csv_file):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("../studies.csv", csv_file)},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_name"


def test_import_csv_rejects_missing_mandatory_fields(client):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("minimal.csv", b"keywords,year\nK1,2020\n")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "missing_mandatory_fields"


def test_import_csv_rejects_blank_record_rows(client):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("gaps.csv", b"title,authors\nT1,A1\n\nT2,A2\n")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "blank_record_row"
    assert response.json()["detail"]["row"] == 3
