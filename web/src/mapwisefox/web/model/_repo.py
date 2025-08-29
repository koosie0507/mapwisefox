from pathlib import Path

import pandas as pd


class PandasRepo:
    def __init__(self, excel_file: Path):
        self._excel_file = excel_file
        self._df = pd.read_excel(excel_file).sort_index(axis=1, inplace=False)
        