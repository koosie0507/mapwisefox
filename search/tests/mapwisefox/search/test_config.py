"""Unit tests for `mapwisefox.search._config.BackendSpec` properties."""

import pytest

from mapwisefox.search._config import BackendRef, BackendSpec


@pytest.mark.parametrize(
    "backend_type",
    ["ConsoleBackend"],
)
def test_is_console_backend_for_console_subclass(backend_type):
    spec = BackendSpec(
        name="console",
        adapter="AcmDSLAdapter",
        backend=BackendRef(type=backend_type),
    )
    assert spec.is_console_backend is True


@pytest.mark.parametrize(
    "backend_type",
    [
        "ScienceDirectBackend",
        "ScopusBackend",
        "SpringerBackend",
        "WebOfScienceBackend",
    ],
)
def test_is_console_backend_for_non_console_without_starter_api(backend_type):
    """Non-Console backends are parallel (not console) unless they are WoS
    with `use_starter_api` falsy."""
    spec = BackendSpec(
        name="api-backend",
        adapter="AcmDSLAdapter",
        backend=BackendRef(type=backend_type),
    )
    # WoS without options defaults `use_starter_api` to falsy → console.
    if backend_type == "WebOfScienceBackend":
        assert spec.is_console_backend is True
    else:
        assert spec.is_console_backend is False


@pytest.mark.parametrize(
    ("use_starter_api", "expected"),
    [
        (False, True),
        (None, True),
        (0, True),
        (True, False),
    ],
    ids=[
        "starter-api-false-is-console",
        "starter-api-omitted-is-console",
        "starter-api-falsy-zero-is-console",
        "starter-api-true-is-parallel",
    ],
)
def test_is_console_backend_wos_use_starter_api_wiring(use_starter_api, expected):
    """Regression test for the `is_console_backend` inverted condition.

    `_wos.py` treats `use_starter_api=False` as console behavior
    (`if not self.__use_starter_api:` prints to stdout and returns). The
    `BackendSpec.is_console_backend` property must agree so that the CLI
    routes WoS-without-starter-api into the sequential console phase.

    A previous bug returned `True` when `use_starter_api` was truthy (inverted),
    which routed the default `use_starter_api: false` WoS backend (as shipped in
    `data/slr-oss/config/search.yaml`) into the parallel phase, interleaving its
    stdout output with concurrent backends.
    """
    options = {}
    if use_starter_api is not None:
        options["use_starter_api"] = use_starter_api
    spec = BackendSpec(
        name="wos",
        adapter="WebOfScienceDSLAdapter",
        backend=BackendRef(type="WebOfScienceBackend", options=options),
    )
    assert spec.is_console_backend is expected


def test_is_console_backend_wos_string_backend_shorthand():
    """WoS via bare-string `backend:` shorthand has no options, so
    `use_starter_api` defaults falsy → console."""
    spec = BackendSpec(
        name="wos-shorthand",
        adapter="WebOfScienceDSLAdapter",
        backend="WebOfScienceBackend",
    )
    assert spec.is_console_backend is True
