import os

from mapwisefox.search.backends import SearchBackend
from mapwisefox.search.query import QueryObject


class ConsoleBackend(SearchBackend):
    def __init__(self):
        super().__init__(False, None)

    def _perform_query(self, query_obj: QueryObject):
        print(
            "The console adapter is used in the absence of an automated way to fetch results"
        )
        print("Copy/paste the query below")
        horizontal_line = "-" * 88
        print(horizontal_line)
        print(query_obj.query)
        print(horizontal_line)
        if query_obj.regex:
            print(f"regex to run on downloaded results: {query_obj.regex}")
            print(horizontal_line)
        if query_obj.filters:
            filter_str = os.linesep.join(
                f"{k}={v}" for k, v in query_obj.filters.items()
            )
            print(f"use these filters in the UI:{os.linesep*2}{filter_str}{os.linesep}")
            print(horizontal_line)
