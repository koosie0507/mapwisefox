from abc import ABCMeta, abstractmethod
from mapwisefox.search.query import QueryObject


class SearchBackend(metaclass=ABCMeta):
    def __init__(self, save_result=False, persistence_adapter=None):
        self._save_result = save_result
        self._persistence_adapter = persistence_adapter

    @abstractmethod
    def _perform_query(self, query_obj: QueryObject):
        raise NotImplementedError()

    def _save(self, results):
        if not self._save_result:
            return
        if self._persistence_adapter is None:
            return
        self._persistence_adapter.save(results)

    def __call__(self, query_obj: QueryObject):
        results = self._perform_query(query_obj)
        self._save(results)
