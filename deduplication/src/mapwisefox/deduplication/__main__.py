from datetime import date, timedelta, datetime
from pathlib import Path

import click

from mapwisefox.deduplication._deduper import (
    _run_dedupe,
    _merge_clusters,
)
from mapwisefox.deduplication._input_loaders import (
    _load_input_files,
)


def _monday():
    return (date.today() - timedelta(days=date.today().weekday())).strftime("%Y%m%d")


@click.command()
@click.option(
    "--input-dir",
    "-I",
    default=Path.cwd() / "data" / "input" / _monday(),
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
)
@click.option(
    "--output-dir",
    "-O",
    default=Path.cwd() / "data" / "output",
    type=click.Path(dir_okay=True, file_okay=False, writable=True),
)
@click.option(
    "--dd-training-file",
    default=Path.cwd() / "data" / "dedupe" / "training.json",
    type=click.Path(dir_okay=False, file_okay=True, writable=True),
)
@click.option(
    "--dd-settings-file",
    default=Path.cwd() / "data" / "dedupe" / "settings.dedupe",
    type=click.Path(dir_okay=False, file_okay=True, writable=True),
)
def main(input_dir, output_dir, dd_training_file, dd_settings_file):
    # input, blocking & filtering
    full_df = _load_input_files(input_dir)

    # matching & clustering
    deduped_df = _run_dedupe(full_df, dd_training_file, dd_settings_file)
    assert len(full_df) == len(deduped_df)

    # profile assembly
    merged_df = _merge_clusters(deduped_df)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now().strftime("%Y%m%d-%H%M%S")}-deduplicated-records.xlsx"
    merged_df.to_excel(output_dir / file_name, sheet_name="all")


if __name__ == "__main__":
    main()
