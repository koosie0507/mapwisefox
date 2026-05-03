import pandas as pd

from mapwisefox.metrics._types import CommonArgs


def save_xls(df: pd.DataFrame, common_args: CommonArgs, sheet_name: str):
    with pd.ExcelWriter(
        common_args.output_file,
        if_sheet_exists="replace" if common_args.output_file.exists() else None,
        mode="a" if common_args.output_file.exists() else "w",
        engine="openpyxl",
    ) as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
