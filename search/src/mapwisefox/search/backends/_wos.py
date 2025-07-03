from functools import partial

import pandas as pd
from clarivate.wos_starter.client import Configuration, ApiClient, DocumentsApi

from mapwisefox.search.adapters import WebOfScienceAdapter
from mapwisefox.search.backends import (
    SearchBackend,
    ConsoleBackend,
)


class WebOfScienceBackend(SearchBackend):
    def __init__(
        self,
        api_key,
        use_starter_api=False,
        save=False,
        persistence_adapter=None,
        **wos_call_params,
    ):
        if api_key is None:
            raise ValueError("api_key is required")
        wos_typ = partial(WebOfScienceAdapter, use_starter_api)
        if use_starter_api:
            persistence_adapter = None
            save = False
        super().__init__(wos_typ, save, persistence_adapter)

        self.__console = ConsoleBackend(wos_typ)
        self.__cfg = Configuration(host="https://api.clarivate.com/apis/wos-starter/v1")
        self.__cfg.api_key["ClarivateApiKeyAuth"] = api_key
        self.__cfg.retries = 1
        self.__use_starter_api = use_starter_api
        self.__call_params = wos_call_params

    def _perform_query(self, query_obj):
        if not self.__use_starter_api:
            self.__console._perform_query(query_obj)
            return pd.DataFrame()

        with ApiClient(self.__cfg) as client:
            api = DocumentsApi(client)

            all_results = []
            params = self.__call_params.copy()
            while (
                len(
                    (
                        resp := api.documents_get(
                            query_obj, _request_timeout=10, **params
                        )
                    ).hits
                )
                > 0
            ):
                all_results.extend(resp.hits)
                params["page"] += 1

            records = [
                {
                    "title": document.title,
                    "authors": "; ".join(
                        a.display_name for a in document.names.authors
                    ),
                    "document_type": "; ".join(document.types),
                    "source": document.source.source_title,
                    "keywords": "; ".join(document.keywords.author_keywords),
                }
                for document in all_results
            ]
            return pd.DataFrame(records)
