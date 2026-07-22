from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

import asyncclick as click
import httpx
import pandas as pd

from meta_paper.adapters import SemanticScholarAdapter


DEFAULT_LINKED_IDS_COLUMN = "referencing_paper_ids"
DETAIL_COLUMNS = [
    "doi",
    "title",
    "authors",
    "abstract",
    "source",
    "url",
    "year",
    "has_pdf",
    "pdf_url",
]
DOI_PREFIXES = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
    "doi:",
)
RELATION_ATTRIBUTES = {"backward": "references", "forward": "citations"}
SHEET_NAMES = {"backward": "Back", "forward": "Forward"}


def _normalize_doi(value):
    if pd.isna(value):
        return None
    identifier = str(value).strip().lower()
    prefix = next((item for item in DOI_PREFIXES if identifier.startswith(item)), "")
    return identifier.removeprefix(prefix) or None


def _read_ids(input_file, sheet_name, id_column):
    try:
        dataframe = pd.read_excel(input_file, sheet_name=sheet_name or 0)
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    if id_column not in dataframe.columns:
        raise click.ClickException(f"Column '{id_column}' was not found")
    return {doi for value in dataframe[id_column] if (doi := _normalize_doi(value))}


def _paper_id(paper):
    return _normalize_doi(paper.doi)


def _relations(papers, direction):
    attribute = RELATION_ATTRIBUTES[direction]
    relations = defaultdict(set)
    for paper in papers:
        source_id = _paper_id(paper)
        if not source_id:
            continue
        for value in getattr(paper, attribute):
            if target_id := _normalize_doi(value):
                relations[target_id].add(source_id)
    return relations


def _merge_links(links, relations, excluded_ids):
    for target_id, source_ids in relations.items():
        if target_id not in excluded_ids:
            links[target_id].update(source_ids - excluded_ids)


async def _snowball(adapter, seed_details, seed_ids, excluded_ids, direction, depth):
    details = {}
    links = defaultdict(set)
    frontier_details = seed_details
    visited = seed_ids | excluded_ids
    for _ in range(depth):
        relations = _relations(frontier_details, direction)
        _merge_links(links, relations, excluded_ids)
        candidates = set(relations) - visited
        visited.update(candidates)
        frontier_details = list(await adapter.get_many(sorted(candidates)))
        details.update(
            (identifier, paper)
            for paper in frontier_details
            if (identifier := _paper_id(paper))
        )
    return details, links


def _to_dataframe(details, links, linked_ids_column):
    columns = [*DETAIL_COLUMNS, linked_ids_column]
    records = [
        _to_record(identifier, details[identifier], links, linked_ids_column)
        for identifier in sorted(details)
    ]
    return pd.DataFrame(records, columns=columns)


def _to_record(identifier, paper, links, linked_ids_column):
    detail = asdict(paper)
    record = {column: detail.get(column) for column in DETAIL_COLUMNS}
    record["doi"] = identifier
    record["authors"] = ";".join(detail.get("authors") or [])
    record["url"] = f"https://doi.org/{identifier}"
    record[linked_ids_column] = ";".join(sorted(links.get(identifier, set())))
    return record


def _output_path(input_file, output_prefix, in_place):
    if in_place:
        return input_file
    return input_file.parent / f"{output_prefix or input_file.stem}-snowball.xlsx"


def _write_output(dataframe, output_file, sheet_name):
    kwargs = (
        {"mode": "a", "if_sheet_exists": "replace"}
        if output_file.is_file()
        else {"mode": "w"}
    )
    with pd.ExcelWriter(output_file, engine="openpyxl", **kwargs) as writer:
        dataframe.to_excel(
            writer, sheet_name=sheet_name, index=True, index_label="cluster_id"
        )


def _warn_about_missing_inputs(seed_ids, seed_details):
    found_ids = {
        identifier for paper in seed_details if (identifier := _paper_id(paper))
    }
    if missing_count := len(seed_ids - found_ids):
        warning = click.style("Warning", fg="yellow")
        click.echo(
            f"{warning}: {missing_count} input IDs were not found using the Semantic Scholar API.",
            color=True,
        )


@click.command(
    help="Perform DOI-based citation snowballing from the INPUT_FILE Excel workbook."
)
@click.argument(
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.option(
    "-e",
    "--exclude",
    "exclude_sheet_name",
    type=click.STRING,
    help="Worksheet containing DOIs to exclude.",
)
@click.option(
    "-s",
    "--sheet-name",
    "sheet_name",
    type=click.STRING,
    help="Worksheet containing the seed paper DOIs.",
)
@click.option(
    "--id-column-name",
    "id_column",
    default="doi",
    show_default=True,
    help="DOI column in the input and exclusion worksheets.",
)
@click.option(
    "-o",
    "--output-prefix",
    type=click.STRING,
    help="Filename prefix for the output workbook.",
)
@click.option(
    "--in-place",
    is_flag=True,
    help="Write the result worksheet into the input workbook.",
)
@click.option(
    "--direction",
    type=click.Choice(["forward", "backward"], case_sensitive=False),
    default="backward",
    show_default=True,
    help="Citation direction to traverse.",
)
@click.option(
    "--max-depth",
    type=click.IntRange(min=1),
    default=1,
    show_default=True,
    help="Maximum number of citation levels to traverse.",
)
@click.option(
    "--linked-ids-column",
    default=DEFAULT_LINKED_IDS_COLUMN,
    show_default=True,
    help="Output column for directly linked paper DOIs.",
)
async def run_command(
    input_file,
    exclude_sheet_name,
    sheet_name,
    id_column,
    output_prefix,
    in_place,
    direction,
    max_depth,
    linked_ids_column,
):
    input_file = Path(input_file).absolute()
    if linked_ids_column in DETAIL_COLUMNS:
        raise click.ClickException(
            f"Linked IDs column '{linked_ids_column}' conflicts with an output column"
        )
    seed_ids = _read_ids(input_file, sheet_name, id_column)
    excluded_ids = (
        _read_ids(input_file, exclude_sheet_name, id_column)
        if exclude_sheet_name
        else set()
    )
    timeout = httpx.Timeout(30.0, connect=2.0)
    client = httpx.AsyncClient(timeout=timeout)
    try:
        adapter = SemanticScholarAdapter(client)
        seed_details = list(await adapter.get_many(sorted(seed_ids)))
        _warn_about_missing_inputs(seed_ids, seed_details)
        details, links = await _snowball(
            adapter,
            seed_details,
            seed_ids,
            excluded_ids,
            direction,
            max_depth,
        )
    finally:
        await client.aclose()
    dataframe = _to_dataframe(details, links, linked_ids_column)
    output_file = _output_path(input_file, output_prefix, in_place)
    _write_output(dataframe, output_file, SHEET_NAMES[direction])
