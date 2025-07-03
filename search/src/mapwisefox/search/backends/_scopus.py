from time import strptime

import pandas as pd
import requests

from mapwisefox.search.adapters import ScopusAdapter
from mapwisefox.search.backends import SearchBackend
from mapwisefox.search.persistence import PandasCsvAdapter


class ScopusBackend(SearchBackend):
    API_ENDPOINT_URL = "https://api.elsevier.com/content/search/scopus"

    def __init__(
        self, api_key, save=True, csv_path="scopus_results.csv", fetch_all=True
    ):
        super().__init__(ScopusAdapter, save, PandasCsvAdapter(csv_path))
        self._session = requests.Session()
        self._session.headers = {
            "X-ELS-APIKey": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._session.params = {"view": "COMPLETE"}
        self._fetch_all = fetch_all

    def _fetch_page(self, query, cursor):
        query_params = {"query": query}
        if cursor:
            query_params["cursor"] = cursor
        response = self._session.get(self.API_ENDPOINT_URL, params=query_params)
        response.raise_for_status()
        return response.json()

    @classmethod
    def _hits(cls, obj):
        return obj["search-results"]["entry"]

    @classmethod
    def _cursor(cls, obj):
        return obj["search-results"].get("cursor", {}).get("@next")

    @classmethod
    def _get_authors(cls, entry):
        return "; ".join(
            {
                f"{author['given-name']}, {author['surname']}"
                for author in entry["author"]
            }
        )

    @classmethod
    def _get_url(cls, entry):
        full_text_urls = set(
            link["@href"]
            for link in entry.get("link", [])
            if link.get("@ref") == "full-text"
        )
        doi_url = (
            f"https://doi.org/{entry['prism:doi']}" if "prism:doi" in entry else "N/A"
        )
        return full_text_urls.pop() if full_text_urls else doi_url

    @classmethod
    def _get_year(cls, entry):
        date = strptime(entry["prism:coverDate"], "%Y-%m-%d")
        return date.tm_year

    def _perform_query(self, query_obj):
        cursor = "*" if self._fetch_all else None
        json_obj = self._fetch_page(query_obj, cursor)
        records = []
        total = int(json_obj["search-results"]["opensearch:totalResults"])
        fetched = len(json_obj["search-results"]["entry"])
        print(f"{fetched} / {total} records fetched")
        while (
            self._fetch_all
            and (cursor := self._cursor(json_obj)) is not None
            and len(hits := self._hits(json_obj)) > 0
        ):
            for entry in hits:
                records.append(
                    {
                        "title": entry["dc:title"],
                        "abstract": entry["dc:description"],
                        "keywords": entry["authkeywords"].replace(" |", ";"),
                        "authors": self._get_authors(entry),
                        "source": entry["prism:publicationName"],
                        "doi": entry.get("prism:doi", "N/A"),
                        "url": self._get_url(entry),
                        "year": self._get_year(entry),
                    }
                )
            fetched += len(hits)
            print(f"{fetched} / {total} records fetched")
            json_obj = self._fetch_page(query_obj, cursor)

        return pd.DataFrame(records)
