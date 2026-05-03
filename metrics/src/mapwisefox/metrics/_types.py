from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class CommonArgs:
    input_files: list[Path] = field(default_factory=list)
    target_attrs: list[str] = field(default_factory=list)
    id_attr: str = "id"
    output_file: Path = ""
    extra_cols: list[str] = field(default_factory=list)
    input_dfs: list[pd.DataFrame] = field(default_factory=list)
