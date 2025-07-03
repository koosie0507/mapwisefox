import pickle

from mapwisefox.search.persistence._base import (
    PersistenceAdapter,
)


class PickleAdapter(PersistenceAdapter):
    def __init__(self, csv_file):
        self._file = csv_file

    def save(self, obj):
        if obj is None:
            raise ValueError("Object cannot be None")
        with open(self._file, mode="wb") as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
