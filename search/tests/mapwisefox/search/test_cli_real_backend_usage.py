from unittest.mock import MagicMock, patch

import pytest
import responses
from click.testing import CliRunner

from mapwisefox.search.__main__ import main


@pytest.mark.parametrize(
    "backend_name,adapter,backend_type,api_key_env,expected_url,expected_headers,mock_response",
    [
        (
            "ScienceDirect",
            "ScienceDirectDSLAdapter",
            "ScienceDirectBackend",
            "MWF_SEARCH_ELSEVIER_API_KEY",
            "https://api.elsevier.com/content/metadata/article",
            {"X-ELS-APIKey": "fake-sd-key", "Accept": "application/json"},
            {"search-results": {"opensearch:itemsPerPage": "0", "entry": []}},
        ),
        (
            "Scopus",
            "ScopusDSLAdapter",
            "ScopusBackend",
            "MWF_SEARCH_ELSEVIER_API_KEY",
            "https://api.elsevier.com/content/search/scopus",
            {"X-ELS-APIKey": "fake-scopus-key", "Accept": "application/json"},
            {
                "search-results": {
                    "opensearch:totalResults": "0",
                    "entry": [],
                }
            },
        ),
        (
            "Springer",
            "SpringerDSLAdapter",
            "SpringerBackend",
            "MWF_SEARCH_SPRINGER_API_KEY",
            "https://api.springernature.com/meta/v2/json",
            {},  # Springer uses query params for API key, not headers
            {"records": [], "result": [{"total": "0"}]},
        ),
    ],
)
@responses.activate
def test_real_backend_makes_correct_http_request(
    single_backend_config_path,
    tmp_path,
    monkeypatch,
    backend_name,
    adapter,
    backend_type,
    api_key_env,
    expected_url,
    expected_headers,
    mock_response,
):
    # Set up API key environment variable
    api_key = f"fake-{backend_name.lower()}-key"
    monkeypatch.setenv(api_key_env, api_key)

    # Mock the HTTP endpoint
    responses.add(
        responses.GET,
        expected_url,
        json=mock_response,
        status=200,
    )

    # Build a minimal config
    config_path = single_backend_config_path(
        query=f'("{backend_name} test query") in title',  # Simple query for this test
        backend_name=backend_name,
        adapter=adapter,
        backend_type=backend_type,
        backend_options={
            "api_key": f"${{{api_key_env}}}",
            "csv_path": f"{backend_name.lower()}.csv",
        },
    )

    # Run the CLI
    runner = CliRunner()
    result = runner.invoke(
        main, ["--config", str(config_path), "--data-dir", str(tmp_path)]
    )

    # Verify success
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    # Verify HTTP request was made
    expected_call_count = 2 if backend_name == "Springer" else 1
    assert (
        len(responses.calls) == expected_call_count
    ), f"Expected {expected_call_count} HTTP call(s), got {len(responses.calls)}"

    # Check the first request (initial query)
    request = responses.calls[0].request

    # Verify URL
    assert request.url.startswith(expected_url), f"Wrong URL: {request.url}"
    # Verify API key (header or query param depending on backend)
    if expected_headers:
        for header, expected_value in expected_headers.items():
            # Skip checking the specific API key value in the test data; use the actual key
            if header in ("X-ELS-APIKey",):
                assert (
                    request.headers.get(header) == api_key
                ), f"Wrong API key in header {header}: {request.headers.get(header)}"
            else:
                assert (
                    request.headers.get(header) == expected_value
                ), f"Missing or wrong header {header}: {request.headers.get(header)}"

    # For Springer, verify API key is in query params
    if backend_name == "Springer":
        assert (
            f"api_key={api_key}" in request.url
        ), f"API key not in Springer query params: {request.url}"

    # Verify CSV file was created
    results_dir = tmp_path / "search-results"
    weekly_dirs = [d for d in results_dir.glob("*") if d.is_dir()]

    if weekly_dirs:
        csv_file = weekly_dirs[0] / f"{backend_name.lower()}.csv"
    else:
        csv_file = results_dir / f"{backend_name.lower()}.csv"

    assert csv_file.exists(), f"CSV file not created at {csv_file}"


@patch("clarivate.wos_starter.client.api.documents_api.DocumentsApi.documents_get")
def test_wos_starter_api_makes_correct_call(
    mock_documents_get,
    single_backend_config_path,
    tmp_path,
    monkeypatch,
):
    # Set up API key
    api_key = "fake-wos-key"
    monkeypatch.setenv("MWF_SEARCH_CLARIVATE_API_KEY", api_key)

    # Mock the API response
    mock_response = MagicMock()
    mock_response.hits = []  # Empty results
    mock_documents_get.return_value = mock_response

    # Build config with WoS starter API enabled
    config_path = single_backend_config_path(
        query='("web of science test") in title',  # Simple query
        backend_name="Web of Science",
        adapter="WebOfScienceDSLAdapter",
        backend_type="WebOfScienceBackend",
        backend_options={
            "api_key": "${MWF_SEARCH_CLARIVATE_API_KEY}",
            "use_starter_api": True,
            "db": "WOS",
            "limit": 50,
            "page": 1,
            "sort_field": "RS+D",
        },
    )

    # Run the CLI
    runner = CliRunner()
    result = runner.invoke(
        main, ["--config", str(config_path), "--data-dir", str(tmp_path)]
    )

    # Verify success
    assert result.exit_code == 0, f"CLI failed: {result.output}"

    # Verify documents_get was called
    assert mock_documents_get.called, "DocumentsApi.documents_get was not called"

    # Verify call arguments
    call_args = mock_documents_get.call_args

    # First positional argument should be the query STRING (not QueryObject)
    actual_query = call_args[0][0]
    assert isinstance(
        actual_query, str
    ), f"Expected query string, got {type(actual_query).__name__}: {actual_query}"

    # Verify the expected kwargs were passed
    assert call_args[1]["db"] == "WOS"
    assert call_args[1]["limit"] == 50
    assert call_args[1]["page"] == 1
    assert call_args[1]["sort_field"] == "RS+D"
    assert "_request_timeout" in call_args[1]
