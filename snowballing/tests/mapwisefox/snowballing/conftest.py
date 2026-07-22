from dataclasses import dataclass, field

import pandas as pd
import pytest
import anyio
from asyncclick.testing import CliRunner


@dataclass
class Paper:
    doi: str
    title: str = "Title"
    authors: list[str] = field(default_factory=lambda: ["Ada", "Grace"])
    abstract: str = "Abstract"
    source: str = "Journal"
    url: str = "https://example.test/paper"
    year: int = 2025
    has_pdf: bool = False
    pdf_url: str | None = None
    citations: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.closed = False

    async def aclose(self):
        self.closed = True


class FakeAdapter:
    def __init__(self, client, papers, calls):
        self.client = client
        self.papers = papers
        self.calls = calls

    async def get_many(self, identifiers):
        identifiers = list(identifiers)
        self.calls.append(identifiers)
        return [
            self.papers[identifier]
            for identifier in identifiers
            if identifier in self.papers
        ]


@pytest.fixture
def runner():
    async_runner = CliRunner()

    class SyncRunner:
        def invoke(self, *args, **kwargs):
            async def invoke():
                return await async_runner.invoke(*args, **kwargs)

            return anyio.run(invoke)

    return SyncRunner()


@pytest.fixture
def adapter(monkeypatch):
    from mapwisefox.snowballing import __cli

    papers = {}
    calls = []
    clients = []

    def client_factory(*args, **kwargs):
        client = FakeClient(*args, **kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr(__cli.httpx, "AsyncClient", client_factory)
    monkeypatch.setattr(
        __cli,
        "SemanticScholarAdapter",
        lambda client: FakeAdapter(client, papers, calls),
    )
    return papers, calls, clients


@pytest.fixture
def workbook(tmp_path):
    def create(rows, *, sheets=None, name="papers.xlsx"):
        path = tmp_path / name
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            pd.DataFrame(rows).to_excel(writer, sheet_name="Papers", index=False)
            for sheet_name, sheet_rows in (sheets or {}).items():
                pd.DataFrame(sheet_rows).to_excel(
                    writer, sheet_name=sheet_name, index=False
                )
        return path

    return create
