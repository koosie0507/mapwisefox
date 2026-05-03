from functools import partial
from pathlib import Path
from typing import Optional, Literal

import pandas as pd
from numpy import clip
from openpyxl import Workbook, load_workbook
from pandas import ExcelWriter

from mapwisefox.web.model import Evidence


type NavigateAction = Literal["first", "prev", "next", "last", "unfilled", "goto"]


class PandasRepo:
    __MANDATORY_COLS = ["include", "exclude_reasons"]

    def __init__(
        self,
        excel_file: Path,
        sheet_name: Optional[str] = None,
        aliases: dict[str, str] = None,
    ):
        self._excel_file = excel_file
        self._sheet_name = sheet_name or self.__read_first_sheet_name()
        excel = pd.read_excel(
            excel_file, sheet_name=self._sheet_name, index_col=0, na_filter=False
        )
        assert isinstance(excel, pd.DataFrame)
        self._df: pd.DataFrame = excel.sort_index(axis=1, inplace=False)
        if aliases is not None:
            self._df.rename(columns=aliases, inplace=True)
        self._aliases = aliases
        self.__infer_cluster_id()
        self.__ensure_mandatory_cols()

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._df

    def get(self, cluster_id: int) -> Evidence:
        params = self._df.loc[cluster_id].to_dict()
        params.update(
            {
                "cluster_id": cluster_id,
            }
        )
        return Evidence(**params)

    @property
    def has_unfilled(self) -> bool:
        return self.navigate(0, "unfilled") >= 0

    @classmethod
    def __safe_int(cls, value):
        if pd.isna(value):
            return -1
        return int(value)

    @classmethod
    def __min_id(cls, df: pd.DataFrame) -> int:
        return cls.__safe_int(df.index.min(skipna=True))

    @classmethod
    def __max_id(cls, df: pd.DataFrame) -> int:
        return cls.__safe_int(df.index.max(skipna=True))

    def __find_first_id(self) -> int:
        return self.__min_id(self._df)

    def __find_next_id(self, current_id: int) -> int:
        return self.__min_id(self._df[self._df.index > current_id])

    def __find_prev_id(self, current_id: int) -> int:
        return self.__max_id(self._df[self._df.index < current_id])

    def __find_last_id(self) -> int:
        return self.__max_id(self._df)

    def __find_next_unfilled(self, current_id: int) -> int:
        include = (
            self._df["include"] if "include" in self._df.columns else pd.Series([])
        )
        next_id = self._df.index > current_id
        next_unfilled_df = self._df[
            ((include.isnull()) | (include.isna()) | (include == "")) & next_id
        ]
        return self.__min_id(next_unfilled_df)

    def navigate(self, cluster_id: int, action: NavigateAction) -> int:
        navigate_actions = {
            "first": self.__find_first_id,
            "prev": partial(self.__find_prev_id, cluster_id),
            "next": partial(self.__find_next_id, cluster_id),
            "last": self.__find_last_id,
            "unfilled": partial(self.__find_next_unfilled, cluster_id),
            "goto": lambda: clip(
                cluster_id, self.__find_first_id(), self.__find_last_id()
            ),
        }
        return navigate_actions[action]()

    def update(self, evidence: Evidence) -> None:
        if evidence.cluster_id not in self._df.index:
            raise KeyError(evidence.cluster_id)
        self._df.loc[evidence.cluster_id] = evidence.model_dump()
        self.__write_xls()

    def __read_first_sheet_name(self) -> str:
        wb: Optional[Workbook] = None
        try:
            wb = load_workbook(filename=self._excel_file, read_only=True)
            return wb.sheetnames[0]
        finally:
            wb.close()

    def __infer_cluster_id(self) -> None:
        if "cluster_id" not in self._df.columns:
            self._df.index.set_names(["cluster_id"], inplace=True)

    def __ensure_mandatory_cols(self) -> None:
        for col in self.__MANDATORY_COLS:
            if col in self._df.columns:
                self._df[col] = self._df[col].astype(str)
            else:
                kw_args = {col: pd.Series([""] * len(self._df), dtype=str)}
                self._df = self._df.assign(**kw_args)

    def __write_xls(self):
        with ExcelWriter(
            self._excel_file, "openpyxl", mode="a", if_sheet_exists="replace"
        ) as writer:
            if isinstance(self._sheet_name, str):
                self._df.to_excel(
                    writer,
                    self._sheet_name,
                    index=True,
                    index_label="cluster_id",
                    na_rep="",
                )
            else:
                self._df.to_excel(
                    writer, index=True, index_label="cluster_id", na_rep=""
                )
