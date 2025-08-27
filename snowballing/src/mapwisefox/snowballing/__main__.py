from pathlib import Path

import click
import pandas as pd


@click.command
@click.argument("input_file", type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.option("-s", "--sheet-name", "sheet_name", type=click.STRING, required=False, default=None)
@click.option("--id-column-name", "id_column", type=click.STRING, required=False, default="doi")
def main(input_file, sheet_name, id_column):
    input_file = Path(input_file).absolute()
    xls = pd.read_excel(input_file, sheet_name=sheet_name)
    identifiers = list(sorted(set(xls[id_column].unique())))
    print(identifiers)


if __name__ == "__main__":
    main()