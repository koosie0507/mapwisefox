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
    from parser import run_dsl
    from parser.backends import ScopusDSLAdapter, SpringerDSLAdapter

    # ── Example 1: simple AND with field restriction ──────────────────────────────
    dsl = '"entity resolution" & "record linkage" in title, abstract'

    scopus_q = run_dsl(dsl, ScopusDSLAdapter())
    springer_q = run_dsl(dsl, SpringerDSLAdapter())

    print(scopus_q)
    # TITLE-ABS("entity resolution") AND TITLE-ABS("record linkage")

    print(springer_q)
    # (title:"entity resolution" OR Abstract:"entity resolution")
    # AND (title:"record linkage" OR Abstract:"record linkage")

    # ── Example 2: output routing ─────────────────────────────────────────────────
    dsl2 = '[-> query: "entity alignment" & "deep learning" in title]'

    result = run_dsl(dsl2, ScopusDSLAdapter())
    # {"query": 'TITLE("entity alignment") AND TITLE("deep learning")', "filter": None}

    api_query = result["query"]  # → send to Scopus API
    post_filter = result["filter"]  # → None, no post-filter

    # ── Example 3: proximity + negation ──────────────────────────────────────────
    dsl3 = 'nearest(5)("entity" & "resolution") & !"survey"'

    print(run_dsl(dsl3, ScopusDSLAdapter()))
    # "entity" W/5 "resolution" AND NOT "survey"

    print(run_dsl(dsl3, SpringerDSLAdapter()))
    # ("entity" "resolution"~5 AND NOT "survey")

    # ── Example 4: regex match routed to filter ───────────────────────────────────
    dsl4 = '[-> filter: match(regex)("entit(y|ies)")]'

    result = run_dsl(dsl4, SpringerDSLAdapter())
    # {"query": None, "filter": '"entit(y|ies)"', "regex": "entit(y|ies)"}

    # Use result["regex"] with re.search() on retrieved abstracts

    # ── Example 5: combining with existing QueryBuilder output ───────────────────
    from mapwisefox.search import QueryBuilder, TitleAbsExpr
    from mapwisefox.search.backends import ScopusBackend

    # Build the base query the old way, then augment with DSL filter
    base_query = (
        QueryBuilder()
        .year_range(2010, 2025)
        .groups(
            QueryBuilder.or_group(
                *map(TitleAbsExpr, ["entity resolution", "record linkage"])
            )
        )
    )

    dsl_filter = run_dsl(
        '[-> filter: match(regex)("framework|architect")]', SpringerDSLAdapter()
    )

    # Pass base_query to the backend, apply dsl_filter["regex"] post-retrieval

    main()
