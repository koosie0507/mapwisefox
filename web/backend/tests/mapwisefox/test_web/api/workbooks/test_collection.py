def test_import_returns_resolved_resource(client, workbook_file):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("studies.xlsx", workbook_file)},
        data={"worksheetName": "Studies", "expectedColumns": "title,abstract"},
    )

    assert response.status_code == 201
    assert response.json()["recordCount"] == 2
    assert response.json()["unfilledRecordCount"] == 2
    assert response.headers["location"] == "/api/v1/workbooks/studies.xlsx"


def test_import_rejects_unresolved_configuration(client, workbook_file):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("studies.xlsx", workbook_file)},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "missing_import_configuration"


def test_import_rejects_invalid_xlsx_content(client):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("broken.xlsx", b"not an xlsx workbook")},
        data={"worksheetName": "Studies", "expectedColumns": "title"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_workbook"


def test_import_persists_selection_criteria(
    client, workbook_file, selection_criteria_json
):
    response = client.post(
        "/api/v1/workbooks",
        files={
            "file": ("studies.xlsx", workbook_file),
            "selectionCriteria": ("criteria.json", selection_criteria_json),
        },
        data={"worksheetName": "Studies", "expectedColumns": "title,abstract"},
    )

    assert response.status_code == 201
    screening = client.get("/api/v1/workbooks/studies.xlsx/screening/0").json()
    assert screening["selectionCriteria"]["review_topic"] == "entity resolution"
    assert screening["selectionCriteria"]["inclusion_criteria"][0]["label"] == "english"


def test_import_accepts_upload_without_selection_criteria(client, workbook_file):
    response = client.post(
        "/api/v1/workbooks",
        files={"file": ("studies.xlsx", workbook_file)},
        data={"worksheetName": "Studies", "expectedColumns": "title,abstract"},
    )

    assert response.status_code == 201
    screening = client.get("/api/v1/workbooks/studies.xlsx/screening/0").json()
    assert screening["selectionCriteria"] is None


def test_import_rejects_malformed_selection_criteria_json(client, workbook_file):
    response = client.post(
        "/api/v1/workbooks",
        files={
            "file": ("studies.xlsx", workbook_file),
            "selectionCriteria": ("criteria.json", b"{not valid json"),
        },
        data={"worksheetName": "Studies", "expectedColumns": "title,abstract"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_selection_criteria"


def test_import_rejects_invalid_selection_criteria_payload(client, workbook_file):
    response = client.post(
        "/api/v1/workbooks",
        files={
            "file": ("studies.xlsx", workbook_file),
            "selectionCriteria": ("criteria.json", b'{"review_topic":"x"}'),
        },
        data={"worksheetName": "Studies", "expectedColumns": "title,abstract"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_selection_criteria"


def test_import_rejects_non_utf8_selection_criteria(client, workbook_file):
    response = client.post(
        "/api/v1/workbooks",
        files={
            "file": ("studies.xlsx", workbook_file),
            "selectionCriteria": ("criteria.json", b"\xff\xfe\x00binary"),
        },
        data={"worksheetName": "Studies", "expectedColumns": "title,abstract"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_selection_criteria"


def test_list_workbooks_tracks_unfilled_records(imported_client):
    response = imported_client.patch(
        "/api/v1/workbooks/studies.xlsx/screening/0",
        json={"decision": "included", "exclusionReasons": []},
    )

    assert response.status_code == 200
    listed = imported_client.get("/api/v1/workbooks").json()

    assert listed[0]["recordCount"] == 2
    assert listed[0]["unfilledRecordCount"] == 1


def test_list_workbooks_reports_complete_workbook(imported_client):
    for index in range(2):
        response = imported_client.patch(
            f"/api/v1/workbooks/studies.xlsx/screening/{index}",
            json={"decision": "included", "exclusionReasons": []},
        )
        assert response.status_code == 200

    listed = imported_client.get("/api/v1/workbooks").json()

    assert listed[0]["unfilledRecordCount"] == 0


def test_reimport_without_prior_delete_refreshes_cached_unfilled_count(
    imported_client, basic_upload, workbook_file
):
    imported_client.patch(
        "/api/v1/workbooks/studies.xlsx/screening/0",
        json={"decision": "included", "exclusionReasons": []},
    )
    previous_unfilled = imported_client.get("/api/v1/workbooks").json()[0][
        "unfilledRecordCount"
    ]

    current_unfilled = basic_upload().json()["unfilledRecordCount"]

    assert previous_unfilled == 1
    assert current_unfilled == 2


def test_reimport_with_prior_delete_refreshes_cached_unfilled_count(
    imported_client, basic_upload, workbook_file
):
    imported_client.patch(
        "/api/v1/workbooks/studies.xlsx/screening/0",
        json={"decision": "included", "exclusionReasons": []},
    )
    previous_unfilled = imported_client.get("/api/v1/workbooks").json()[0][
        "unfilledRecordCount"
    ]
    imported_client.delete("/api/v1/workbooks/studies.xlsx")

    current_unfilled = basic_upload().json()["unfilledRecordCount"]

    assert previous_unfilled == 1
    assert current_unfilled == 2
