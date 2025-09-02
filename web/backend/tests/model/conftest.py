from datetime import datetime, UTC
from pathlib import Path
from typing import Callable

import pytest

from mapwisefox.web.model import Evidence


@pytest.fixture(scope="session")
def new_evidence() -> Callable[[...], Evidence]:
    def _evidence_factory(
            cluster_id,
            include=False,
            doi="10.1016/j.cpc.2019.01.011",
            title="test title",
            abstract="test abstract",
            authors=["test author"],
            keywords=["test keyword"],
            publication_date=datetime.now(UTC),
            publication_venue="test venue",
            url="https://doi.org/10.1016/j.cpc.2019.01.011",
            has_pdf=True,
            pdf_url="https://example.com/10.1016/j.cpc.2019.01.011/pdf",
            exclude_reasons=["reason 1", "reason 2"],
            referencing_evidence=None,
    ):
        return Evidence(
            cluster_id=cluster_id,
            include=include,
            doi=doi,
            title=title,
            abstract=abstract,
            authors=authors,
            keywords=keywords,
            publication_date=publication_date,
            publication_venue=publication_venue,
            url=url,
            has_pdf=has_pdf,
            pdf_url=pdf_url,
            exclude_reasons=exclude_reasons,
            referencing_evidence=referencing_evidence,
        )
    return _evidence_factory


@pytest.fixture(scope="session")
def datadir():
    return Path(__file__).parent / "data"
