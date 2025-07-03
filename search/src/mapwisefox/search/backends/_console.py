from mapwisefox.search.backends._base import SearchBackend


class ConsoleBackend(SearchBackend):
    def __init__(self, query_adapter_type):
        super().__init__(query_adapter_type, False, None)

    def _perform_query(self, query_obj):
        print(
            "The console adapter is used in the absence of an automated way to fetch results"
        )
        print("Copy/paste the query below")
        print("-" * 80)
        print(query_obj)
        print("-" * 80)
