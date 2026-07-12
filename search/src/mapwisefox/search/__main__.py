import datetime
from functools import partial
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import click
import dotenv

from mapwisefox.search import (
    QueryBuilder,
    EvidenceTypes,
    SubjectAreas,
    TitleAbsExpr,
)
from mapwisefox.search.adapters.query_builder import (
    ACMAdapter,
    ScienceDirectAdapter,
    ScopusAdapter,
    SpringerAdapter,
    WebOfScienceAdapter,
    XploreAdapter,
)
from mapwisefox.search.backends.query_builder import (
    ConsoleBackend,
    WebOfScienceBackend,
    ScopusBackend,
    ScienceDirectBackend,
    SpringerBackend,
)
from mapwisefox.search.persistence import PandasCsvAdapter

dotenv.load_dotenv()


def _query_builder():
    er_terms = [
        "entity resolution",
        "entity alignment",
        "record linkage",
        "data deduplication",
        "merge/purge",
        "entity linking",
        "entity matching",
    ]
    qualifiers = ["system", "tool*", "framework", "architect*", "library"]
    query = QueryBuilder().year_range(2010, 2025)
    query.groups(
        query.and_group(
            query.or_group(*map(TitleAbsExpr, er_terms)),
            query.or_group(*map(TitleAbsExpr, qualifiers)),
        )
    ).doc_types(
        EvidenceTypes.ARTICLE,
        EvidenceTypes.CONFERENCE,
    ).subject_areas(
        SubjectAreas.COMPUTER_SCIENCE
    ).languages(
        "english"
    ).keywords(
        *er_terms
    )
    return query


def _monday():
    return (
        datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
    ).strftime("%Y%m%d")


def _ensure_input_dir(data_dir):
    input_dir = Path(data_dir) / "input" / _monday()
    input_dir.mkdir(parents=True, exist_ok=True)
    return input_dir


def _ersa_qb_search_configs(data_dir, elsevier_api_key, springer_api_key, clarivate_api_key):
    qb = _query_builder()
    yield (
        "ScienceDirect",
        ScienceDirectBackend(
            api_key=elsevier_api_key,
            csv_path=_ensure_input_dir(data_dir) / "science_direct.csv",
        ),
        qb.build(ScienceDirectAdapter)
    )
    yield (
        "Springer",
        SpringerBackend(
            api_key=springer_api_key,
            csv_path=_ensure_input_dir(data_dir) / "springer.csv",
            fetch_all=True,
        ),
        qb.build(SpringerAdapter)
    )
    yield (
        "Scopus",
        ScopusBackend(
            api_key=elsevier_api_key,
            csv_path=_ensure_input_dir(data_dir) / "scopus.csv",
        ),
        qb.build(ScopusAdapter)
    )
    yield "ACM", ConsoleBackend(), qb.build(ACMAdapter)
    yield (
        "IEEE Xplore",
        ConsoleBackend(),
        qb.build(ScienceDirectAdapter)
    )
    yield (
        "Web of Science",
        WebOfScienceBackend(
            api_key=clarivate_api_key,
            use_starter_api=False,
            save=False,
            persistence_adapter=PandasCsvAdapter(
                _ensure_input_dir(data_dir) / "wos-api.csv"
            ),
            db="WOS",
            limit=50,
            page=1,
            sort_field="RS+D",
        ),
        qb.build(WebOfScienceAdapter)
    )


@click.command("search")
@click.option("--clarivate-api-key", envvar="MWF_SEARCH_CLARIVATE_API_KEY")
@click.option("--elsevier-api-key", envvar="MWF_SEARCH_ELSEVIER_API_KEY")
@click.option("--springer-api-key", envvar="MWF_SEARCH_SPRINGER_API_KEY")
@click.option("--data-dir", "-D", default=Path().cwd() / "data", envvar="DATA_DIR")
def main(clarivate_api_key, elsevier_api_key, springer_api_key, data_dir):
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_dict = {
            executor.submit(backend, query_obj): name
            for name, backend, query_obj in _ersa_qb_search_configs(
                data_dir, elsevier_api_key, springer_api_key, clarivate_api_key
            )
        }
        for future in as_completed(future_dict):
            name = future_dict[future]
            try:
                future.done()
            except Exception as exc:
                print(f"error occured in {name} backend: {exc}")
            else:
                print(name, "completed without errors")


if __name__ == "__main__":
    main()
