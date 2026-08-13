from datetime import datetime
from pathlib import Path

import click

from mapwisefox.deduplication._deduper import (
    _run_dedupe,
    _merge_clusters,
)
from mapwisefox.deduplication._input_loaders import (
    _load_input_files,
)


DEDUPE_SETTINGS_FILE = "settings.dedupe"
DEDUPE_TRAINING_CONFIG = "training.json"


def _default_output_file():
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path.cwd() / "data" / "output" / f"{timestamp}-deduplicated-records.xlsx"


@click.command(
    help="Deduplicate results from multiple academic search sources into a single spreadsheet."
)
@click.option(
    "--input-dir",
    "-I",
    default=Path.cwd() / "data" / "input",
    type=click.Path(dir_okay=True, file_okay=False),
    help="Directory containing .csv or .bib files to merge and deduplicate.",
)
@click.option(
    "--output-file",
    "-o",
    default=None,
    type=click.Path(dir_okay=False, file_okay=True, writable=True),
    help="Path to the output deduplicated .xlsx file. Defaults to a timestamped file in ./data/output.",
)
@click.option(
    "--dd-config-dir",
    default=Path.cwd() / "dedupe",
    type=click.Path(dir_okay=True, file_okay=False, writable=True),
    help="Directory containing the dedupe config (training.json and settings.dedupe).",
)
@click.option(
    "--threshold",
    default=0.5,
    type=click.FloatRange(0.0, 1.0),
    help="Similarity score threshold (0-1) for treating two records as duplicates.",
)
@click.option(
    "--field",
    "-f",
    "fields",
    default=None,
    type=click.STRING,
    multiple=True,
    help="One or more string fields to deduplicate on",
)
def main(input_dir, output_file, dd_config_dir, threshold, fields):
    # input, blocking & filtering
    input_dir = Path(input_dir)
    output_file = Path(output_file) if output_file else _default_output_file()
    dd_config_dir = Path(dd_config_dir)
    dd_training_file = dd_config_dir / DEDUPE_TRAINING_CONFIG
    dd_settings_file = dd_config_dir / DEDUPE_SETTINGS_FILE

    if not input_dir.is_dir():
        raise click.UsageError(f"Input directory {input_dir} does not exist.")

    full_df = _load_input_files(input_dir)
    if full_df.empty:
        raise click.UsageError(f"No .csv or .bib files found in {input_dir}.")

    # matching & clustering
    deduped_df = _run_dedupe(
        full_df, dd_training_file, dd_settings_file, threshold=threshold, fields=fields
    )
    assert len(full_df) == len(deduped_df)

    # profile assembly
    merged_df = _merge_clusters(deduped_df)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_excel(output_file, sheet_name="all")


if __name__ == "__main__":
    main()
