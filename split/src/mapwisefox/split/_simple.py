from pathlib import Path

import click
import numpy as np
import pandas as pd


@click.command(name="simple")
@click.option(
    "--input-dir",
    "-D",
    default=Path.cwd() / "data" / "output",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
)
@click.option(
    "--include",
    "-I",
    default="*-deduplicated-records.xlsx",
    type=click.STRING,
)
@click.option(
    "--split-count",
    "-n",
    default=2,
    type=click.INT,
)
def simple(input_dir, include, split_count) -> None:
    input_dir = Path(input_dir)
    splits_dir = input_dir / "splits"

    for file in input_dir.glob(include):
        click.echo("processing splits for {}".format(file.stem))
        df = pd.read_excel(file)
        file_splits_dir = splits_dir / file.stem
        file_splits_dir.mkdir(parents=True, exist_ok=True)
        splits = np.array_split(df.sample(frac=1), split_count)
        for split_no, split in enumerate(splits, 1):
            split_path = file_splits_dir / f"{split_no:04}.xlsx"
            split.set_index("cluster_id", inplace=True)
            split.to_excel(split_path)
            click.echo(
                "saved split {} of {} to {}".format(split_no, len(splits), split_path)
            )
    click.echo("done")