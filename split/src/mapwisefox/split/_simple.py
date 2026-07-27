from pathlib import Path

import click
import numpy as np
import pandas as pd


@click.command(name="simple")
@click.option(
    "--input-dir",
    "-D",
    default=lambda: Path.cwd() / "data" / "output",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
    show_default=True,
    help="Directory containing the Excel workbooks to split.",
)
@click.option(
    "--include",
    "-I",
    default="*-deduplicated-records.xlsx",
    type=click.STRING,
    show_default=True,
    help="Filename pattern for input workbooks.",
)
@click.option(
    "--split-count",
    "-n",
    default=2,
    type=click.IntRange(min=1),
    show_default=True,
    help="Number of non-overlapping reviewer bundles to create.",
)
def simple(input_dir: str | Path, include: str, split_count: int) -> None:
    """Randomly divide matching workbooks into non-overlapping bundles."""
    input_dir = Path(input_dir)
    splits_dir = input_dir / "splits"

    for file in input_dir.glob(include):
        click.echo("processing splits for {}".format(file.stem))
        df = pd.read_excel(file)
        if "cluster_id" not in df.columns:
            raise click.ClickException(
                f"Input workbook {file} must contain a 'cluster_id' column."
            )
        file_splits_dir = splits_dir / file.stem
        file_splits_dir.mkdir(parents=True, exist_ok=True)
        splits = np.array_split(df.sample(frac=1), split_count)
        for split_no, split in enumerate(splits, 1):
            split_path = file_splits_dir / f"{split_no:04}.xlsx"
            split.set_index("cluster_id").to_excel(split_path)
            click.echo(
                "saved split {} of {} to {}".format(split_no, len(splits), split_path)
            )
    click.echo("done")
