import re
from functools import partial
from time import sleep, strptime

import pandas as pd
import requests

from mapwisefox.search.adapters import SpringerAdapter
from mapwisefox.search.backends import SearchBackend
from mapwisefox.search.persistence import PandasCsvAdapter


class SpringerBackend(SearchBackend):
    def __init__(self, api_key, csv_path=None, is_premium=False, fetch_all=True):
        super().__init__(
            partial(SpringerAdapter, is_premium),
            csv_path is not None,
            PandasCsvAdapter(csv_path) if csv_path is not None else None,
        )
        self._page_size = 25
        self._params = {"api_key": api_key, "p": self._page_size}
        self._session = requests.Session()
        self._api_url = "https://api.springernature.com/meta/v2/json"
        self._session.params = self._params
        self._retry_count = 5
        self.__fetch_all = fetch_all

    def _fetch_one_page(self, query, page_no, retry_no=0):
        start = page_no * self._page_size + 1
        resp = self._session.get(self._api_url, params={"q": query, "s": start})
        if resp.status_code == 429 and retry_no < self._retry_count:
            seconds = pow(3, retry_no + 1)
            print("got 429, sleeping ", seconds, "seconds before retrying...")
            sleep(seconds)
            return self._fetch_one_page(query, page_no, retry_no + 1)
        resp.raise_for_status()
        return resp.json()

    def _local_filter(self, regex, record):
        title, abstract = record["title"], record["abstract"]
        title_match = regex.match(title)
        abstract_match = regex.match(abstract)
        return title_match or abstract_match

    def _perform_query(self, query_obj):
        results = []
        try:
            data = self._fetch_one_page(query_obj["query"], 0, retry_no=1)
            results.extend(data["records"])
            stats = data.get("result", [])
            if len(stats) == 0:
                raise Exception("No results found")
            total = int(stats[0].get("total", 0))
            page = 1
            while (
                self.__fetch_all
                and len(
                    data := self._fetch_one_page(query_obj["query"], page, retry_no=1)
                )
                > 0
                and len(results) < total
            ):
                results.extend(data["records"])
                page += 1
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("exceeded retry count... working with what we've got so far")

        regex_filter = re.compile(query_obj["regex"], re.I)
        results = filter(partial(self._local_filter, regex_filter), results)

        def _get_url(record):
            urls = set(
                fmt.get("value", "")
                for fmt in record["url"]
                if fmt.get("format") == "html"
            )
            doi = record.get("doi")
            return urls.pop() if urls else f"https://doi.org/{doi}" if doi else "N/A"

        def _get_year(record):
            pub_date = strptime(record["publicationDate"], "%Y-%m-%d")
            return pub_date.tm_year

        records = [
            {
                "title": result["title"],
                "abstract": result["abstract"],
                "keywords": "; ".join(x.strip() for x in result["keyword"]),
                "authors": "; ".join(x["creator"].strip() for x in result["creators"]),
                "source": result["publicationName"],
                "doi": result.get("doi", "N/A"),
                "url": _get_url(result),
                "year": _get_year(result),
            }
            for result in results
        ]

        return pd.DataFrame(records)
