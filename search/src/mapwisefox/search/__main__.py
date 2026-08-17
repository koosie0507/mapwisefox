import datetime
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import click
import dotenv
import yaml

from mapwisefox.search._config import BackendSpec, SearchConfig
from mapwisefox.search.backends import SearchBackend
from mapwisefox.search.dsl.parser import Parser
from mapwisefox.search.dsl.parser._ir import Query as QueryIR
from mapwisefox.search.persistence import PandasCsvAdapter
from mapwisefox.search.query import QueryObject


dotenv.load_dotenv()

logger = logging.getLogger("mapwisefox.search")


def _expand_env(value: Any) -> Any:
    """Recursively expand ``${VAR}``/``$VAR`` references from the environment."""
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def _load_config(config_path: Path) -> SearchConfig:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config = SearchConfig.model_validate(raw)
    if config.query_file:
        query_file_path = Path(config.query_file)
        if not query_file_path.is_absolute():
            query_file_path = config_path.parent / query_file_path
        config.query = query_file_path.read_text(encoding="utf-8")
    return config


def _monday() -> str:
    today = datetime.date.today()
    return (today - datetime.timedelta(days=today.weekday())).strftime("%Y%m%d")


def _ensure_results_dir(
    data_dir: str | Path, results_dir_name: str, use_weekly_buckets: bool
) -> Path:
    results_dir = Path(data_dir) / results_dir_name
    if use_weekly_buckets:
        results_dir = results_dir / _monday()
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def _resolve_backend_options(spec: BackendSpec, input_dir: Path) -> dict[str, Any]:
    """Expand env vars and resolve path-like options against the input dir."""
    options = _expand_env(spec.backend_options)
    if isinstance(options.get("csv_path"), (str, Path)):
        options["csv_path"] = input_dir / options["csv_path"]
    if isinstance(options.get("persistence_adapter"), (str, Path)):
        options["persistence_adapter"] = PandasCsvAdapter(
            input_dir / options["persistence_adapter"]
        )
    return options


def _build_backend(spec: BackendSpec, input_dir: Path) -> SearchBackend:
    options = _resolve_backend_options(spec, input_dir)
    return spec.backend_cls(**options)


def _build_query_object(spec: BackendSpec, ir: QueryIR) -> QueryObject:
    adapter_options = _expand_env(spec.adapter_options)
    adapter = spec.adapter_cls(**adapter_options)
    return adapter.adapt(ir)


def _execute(spec: BackendSpec, ir: QueryIR, input_dir: Path) -> None:
    backend = _build_backend(spec, input_dir)
    query_obj = _build_query_object(spec, ir)
    logger.info("running backend %s", spec.name)
    backend(query_obj)


@click.command(
    "search",
    help=r"""
Runs configured search backends against the specified query and saves results.

The results are written under <data-dir>/<results-dir-name>/<week start date>.
The week start date is the date the most recent Monday falls on. Running search
multiple times during the same week overwrites previous results by default. This
enables rapid iteration. This behaviour can be turned off using the
--disable-weekly-bucket flag.
""",
)
@click.option(
    "--config",
    "-c",
    "config_path",
    required=True,
    envvar="MWF_SEARCH_CONFIG",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the YAML search configuration file.",
)
@click.option(
    "--data-dir",
    "-D",
    default=Path().cwd() / "data",
    envvar="DATA_DIR",
    help="Root directory results are written under.",
)
@click.option(
    "--max-workers",
    default=3,
    show_default=True,
    help="Maximum number of backends to run concurrently.",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    default=False,
    help="If set, detailed errors from all backends will be printed.",
)
@click.option(
    "--disable-weekly-bucket",
    "disable_weekly",
    is_flag=True,
    default=False,
    help="If set, results will be written to the --results-dir-name subdirectory.",
)
@click.option(
    "--results-dir-name",
    default="search-results",
    help="The subdirectory name within --data-dir where results are written.",
)
def main(
    config_path: Path,
    data_dir: str | Path,
    max_workers: int,
    debug: bool,
    disable_weekly: bool,
    results_dir_name: str,
):
    logging.basicConfig(
        level=logging.INFO if not debug else logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = _load_config(config_path)
    search_results_dir = _ensure_results_dir(
        data_dir, results_dir_name, not disable_weekly
    )

    assert config.query is not None  # guaranteed by SearchConfig validation
    parser = Parser()
    ir = parser(config.query)

    console_specs = [spec for spec in config.backends if spec.is_console_backend]
    parallel_specs = [spec for spec in config.backends if not spec.is_console_backend]
    for spec in console_specs:
        try:
            _execute(spec, ir, search_results_dir)
        except Exception:
            logger.exception("error occurred in %s backend", spec.name)
        else:
            logger.info("%s completed without errors", spec.name)

    if not parallel_specs:
        return

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_spec = {
            executor.submit(_execute, spec, ir, search_results_dir): spec
            for spec in parallel_specs
        }
        errors = []
        for future in as_completed(future_to_spec):
            spec = future_to_spec[future]
            try:
                future.result()
            except Exception as exc:
                errors.append((spec.name, exc))
                logger.warning("%s failed", spec.name)
            else:
                logger.info("%s completed without errors", spec.name)
        if errors and debug:
            for err in errors:
                logger.debug("%s error", exc_info=err)


if __name__ == "__main__":
    main()
