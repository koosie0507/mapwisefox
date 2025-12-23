from dataclasses import asdict
from functools import reduce, partial
from pathlib import Path

import asyncclick as click
import httpx
import pandas as pd

from meta_paper.adapters import SemanticScholarAdapter


def __sanitize_detail(paper_details):
    paper_details.url = paper_details.doi.replace("DOI:", "https://dx.doi.org/")
    return paper_details


def __add_ref(result, paper, selector):
    if result is None:
        result = {}
    for identifier in selector(paper):
        if identifier not in result:
            result[identifier] = set()
        result[identifier].add(paper.doi)
    return result


def __transform_details(ref_map, details):
    result = []
    for detail in details:
        referencing_papers = ref_map.get(detail["doi"], [])
        referencing_papers = list(map(__remove_doi_prefix, referencing_papers))
        detail["referencing_paper_ids"] = ";".join(referencing_papers)
        detail["authors"] = ";".join(detail.get("authors", []))
        del detail["citations"]
        del detail["references"]
        result.append(__remove_doi_prefix(detail))

    return result


def __remove_doi_prefix(detail):
    if isinstance(detail, dict) and "doi" in detail:
        detail["doi"] = detail["doi"].replace("DOI:", "")
    if isinstance(detail, str):
        return detail.replace("DOI:", "")
    return detail


@click.command
@click.argument(
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.option(
    "-e",
    "--exclude",
    "exclude_sheet_name",
    type=click.STRING,
    required=False,
    default=None,
)
@click.option(
    "-s", "--sheet-name", "sheet_name", type=click.STRING, required=False, default=None
)
@click.option(
    "--id-column-name", "id_column", type=click.STRING, required=False, default="doi"
)
@click.option("-o", "--output-prefix", type=click.STRING, required=False, default=None)
@click.option(
    "--in-place", type=click.BOOL, required=False, default=False, is_flag=True
)
async def run_command(
    input_file, exclude_sheet_name, sheet_name, id_column, output_prefix, in_place
):
    input_file = Path(input_file).absolute()
    output_prefix = output_prefix or input_file.stem

    xls = pd.read_excel(input_file, sheet_name=sheet_name)

    unique_ids = set(xls[id_column].unique())
    excluded_unique_ids = set()
    if exclude_sheet_name:
        excluded_unique_ids = set(
            pd.read_excel(input_file, sheet_name=exclude_sheet_name)[id_column].unique()
        )

    sorted_ids = list(sorted(unique_ids))
    timeout = httpx.Timeout(30.0, connect=2.0)
    adp = SemanticScholarAdapter(httpx.AsyncClient(timeout=timeout))
    paper_info = list(await adp.get_many(sorted_ids))
    if len(paper_info) != len(unique_ids):
        not_found_count = len(unique_ids) - len(paper_info)
        styled_warning_text = click.style("Warning", fg="yellow")
        click.echo(
            f"{styled_warning_text}: {not_found_count} input IDs were not found using the Semantic Scholar API.",
            color=True,
        )
    put_citations = partial(__add_ref, selector=lambda paper: paper.citations)
    put_refs = partial(__add_ref, selector=lambda paper: paper.references)
    citations_map = reduce(put_citations, paper_info, dict())
    references_map = reduce(put_refs, paper_info, dict())
    all_refs = set(references_map)
    all_citations = set(citations_map)

    backward_snowball = all_refs - all_citations - unique_ids - excluded_unique_ids
    backward_details = __transform_details(
        references_map,
        map(asdict, map(__sanitize_detail, await adp.get_many(backward_snowball))),
    )
    backward_df = pd.DataFrame(backward_details)

    forward_snowball = all_citations - all_refs - unique_ids - excluded_unique_ids
    forward_details = __transform_details(
        citations_map, map(asdict, await adp.get_many(forward_snowball))
    )
    forward_df = pd.DataFrame(forward_details)

    output_file = (
        input_file.parent / f"{output_prefix}-snowball.xlsx"
        if not in_place
        else input_file
    )
    with pd.ExcelWriter(
        output_file, engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as xls_writer:
        backward_df.to_excel(xls_writer, sheet_name="Back")
        forward_df.to_excel(xls_writer, sheet_name="Forward")
