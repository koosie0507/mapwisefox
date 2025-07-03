import pandas as pd

from mapwisefox.search.persistence._base import (
    PersistenceAdapter,
)


class PandasCsvAdapter(PersistenceAdapter):
    def __init__(self, csv_file):
        self._file = csv_file

    def save(self, obj):
        if obj is None or not isinstance(obj, pd.DataFrame):
            raise TypeError("Object must be of type pandas.DataFrame")

        obj.to_csv(self._file, index=False)
