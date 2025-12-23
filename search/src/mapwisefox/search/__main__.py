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
from mapwisefox.search.adapters import (
    XploreAdapter,
    ACMAdapter,
)
from mapwisefox.search.backends import (
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


def _wos(data_dir, api_key, use_starter_api=False):
    search = WebOfScienceBackend(
        api_key,
        use_starter_api,
        save=use_starter_api,
        persistence_adapter=PandasCsvAdapter(
            _ensure_input_dir(data_dir) / "wos-api.csv"
        ),
        db="WOS",
        limit=50,
        page=1,
        sort_field="RS+D",
    )
    search(_query_builder())


def _scopus(data_dir, api_key):
    search = ScopusBackend(
        api_key,
        csv_path=_ensure_input_dir(data_dir) / "scopus.csv",
    )
    search(_query_builder())


def _science_direct(data_dir, api_key):
    search = ScienceDirectBackend(
        api_key,
        csv_path=_ensure_input_dir(data_dir) / "science_direct.csv",
    )
    search(_query_builder())


def _xplore():
    search = ConsoleBackend(XploreAdapter)
    search(_query_builder())


def _acm():
    search = ConsoleBackend(ACMAdapter)
    search(_query_builder())


def _springer(data_dir, api_key, fetch_all=True):
    search = SpringerBackend(
        api_key,
        csv_path=_ensure_input_dir(data_dir) / "springer.csv",
        fetch_all=fetch_all,
    )
    search(_query_builder())


@click.command("search")
@click.option("--clarivate-api-key", envvar="MWF_SEARCH_CLARIVATE_API_KEY")
@click.option("--elsevier-api-key", envvar="MWF_SEARCH_ELSEVIER_API_KEY")
@click.option("--springer-api-key", envvar="MWF_SEARCH_SPRINGER_API_KEY")
@click.option("--data-dir", "-D", default=Path().cwd() / "data", envvar="DATA_DIR")
def main(clarivate_api_key, elsevier_api_key, springer_api_key, data_dir):
    api_backends = {
        partial(
            _science_direct, data_dir=data_dir, api_key=elsevier_api_key
        ): "ScienceDirect",
        partial(_springer, data_dir=data_dir, api_key=springer_api_key): "Springer",
        partial(_scopus, data_dir=data_dir, api_key=elsevier_api_key): "Scopus",
    }
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_dict = {executor.submit(f): name for f, name in api_backends.items()}
        for future in as_completed(future_dict):
            name = future_dict[future]
            try:
                future.done()
            except Exception as exc:
                print(f"error occured in {name} backend: {exc}")
            else:
                print(name, "completed without errors")

    ui_backends = {
        _acm: "ACM",
        _xplore: "IEEE Xplore",
        partial(
            _wos, data_dir=data_dir, api_key=clarivate_api_key, use_starter_api=False
        ): "Web of Science",
    }
    for f, name in ui_backends.items():
        print(name)
        f()


if __name__ == "__main__":
    main()
