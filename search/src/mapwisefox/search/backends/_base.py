from abc import ABCMeta, abstractmethod


class SearchBackend(metaclass=ABCMeta):
    def __init__(self, query_adapter_type, save_result=False, persistence_adapter=None):
        self._query_adapter_type = query_adapter_type
        self._save_result = save_result
        self._persistence_adapter = persistence_adapter

    @abstractmethod
    def _perform_query(self, query_obj):
        raise NotImplementedError()

    def _save(self, results):
        if not self._save_result:
            return
        if self._persistence_adapter is None:
            return
        self._persistence_adapter.save(results)

    def __call__(self, query_builder):
        query_obj = query_builder.build(self._query_adapter_type)
        results = self._perform_query(query_obj)
        self._save(results)
