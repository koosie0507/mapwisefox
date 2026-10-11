RECORD_FIELDS = (
    "title",
    "abstract",
    "authors",
    "keywords",
    "source",
    "year",
    "doi",
    "url",
    "has_pdf",
)

_PROVIDER_HEADERS = {
    "author full names": "authors",
    "author names": "authors",
    "article title": "title",
    "document title": "title",
    "source title": "source",
    "publication title": "source",
    "abbreviated source title": "source",
    "author keywords": "keywords",
    "index keywords": "keywords",
    "keywords plus": "keywords",
    "publication year": "year",
    "doi link": "url",
    "pdf link": "url",
    "link": "url",
}

DEFAULT_HEADER_ALIASES = {
    **{field: field for field in RECORD_FIELDS},
    **_PROVIDER_HEADERS,
}


def normalize_header(header):
    return str(header).strip().casefold()


def resolve_headers(headers, aliases=DEFAULT_HEADER_ALIASES):
    """Resolve worksheet headers to canonical record fields.

    Scans headers left to right, mapping the first header that resolves to a
    canonical field; unresolved headers are kept as-is.
    """
    resolved = {}
    for header in headers:
        field = aliases.get(normalize_header(header))
        if field and field not in resolved.values():
            resolved[str(header)] = field
    return resolved
