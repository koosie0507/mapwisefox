from time import strptime

import pandas as pd
import requests

from mapwisefox.search.adapters import ScienceDirectAdapter
from mapwisefox.search.backends import SearchBackend
from mapwisefox.search.persistence import PandasCsvAdapter


class ScienceDirectBackend(SearchBackend):
    def __init__(self, api_key, save=True, csv_path="scopus_results.csv"):
        super().__init__(ScienceDirectAdapter, save, PandasCsvAdapter(csv_path))
        self.__api_key = api_key

    def _sd_fetch_one_page(self, query_params):
        response = requests.get(
            "https://api.elsevier.com/content/metadata/article",
            params=query_params,
            headers={
                "X-ELS-APIKey": self.__api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["search-results"]

    def _perform_query(self, query_obj):
        page_size = 10
        query_params = {
            "start": 0,
            "count": page_size,
            "view": "COMPLETE",
            **query_obj,
        }
        results = []
        while (
            int(
                (page_results := self._sd_fetch_one_page(query_params)).get(
                    "opensearch:itemsPerPage", 0
                )
            )
            > 0
        ):
            results.extend(page_results.get("entry"))
            query_params["start"] += page_size
        records = []

        def get_authors(record):
            authors = record.get("authors", {})
            author = authors.get("author", [])
            return "; ".join(a["$"] for a in author)

        def get_url(record):
            urls = set(link.get("@href", "") for link in record.get("link", []))
            doi_url = (
                f"https://doi.org/{record["prism:doi"].lower()}"
                if "prism:doi" in record
                else "N/A"
            )
            return urls.pop() if urls else doi_url

        def get_year(record):
            date = strptime(record["available-online-date"], "%Y-%m-%d")
            return date.tm_year

        for result in results:
            records.append(
                {
                    "title": result["dc:title"],
                    "abstract": result["dc:description"],
                    "keywords": "; ".join(
                        map(
                            lambda x: x.strip(),
                            result.get("authkeywords", "").split("|"),
                        )
                    ),
                    "authors": get_authors(result),
                    "source": result["prism:publicationName"],
                    "url": get_url(result),
                    "doi": result.get("prism:doi", "N/A"),
                    "year": get_year(result),
                }
            )
        return pd.DataFrame(records)
