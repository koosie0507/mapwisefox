from mapwisefox.search.backends.query_builder._base import SearchBackend


class ConsoleBackend(SearchBackend):
    def __init__(self):
        super().__init__(False, None)

    def _perform_query(self, query_obj):
        print(
            "The console adapter is used in the absence of an automated way to fetch results"
        )
        print("Copy/paste the query below")
        print("-" * 80)
        print(query_obj)
        print("-" * 80)
