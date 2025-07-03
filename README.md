# MapwiseFox

MapwiseFox is a suite of tools that aims to alleviate the process of creating
systematic literature reviews. It is primarily aimed at the software engineering
field, but there's nothing preventing researchers, academics and practitioners
from other fields to use it.

The package provides the following utilities geared at key steps in the
systematic literature review process:

- [x] `mws-search` - allows searching one or more online databases using the 
same input query (write the query once, search it across multiple DBs) :rocket:.
- [x] `mws-deduplicate` - deduplicates the search results retrieved from
multiple databases.
- [x] `mws-split` - basic data splitter which allows assigning smaller workloads
to the team of reviewers.

The cornerstone of the suite is the homonymous application aimed at easing the
selection of primary studies, their evaluation as well as the extraction of data
attributes from each study.

## Running

Python 3.13 and [`uv`](https://docs.astral.sh/uv/) are required.

```shell
$ make bootstrap
$ uv run web -D <local path where you want to store files> 
```


## Contributing

The code repository for this package is hosted on GitHub. E-mail the authors to
gain access and then head on to `CONTRIBUTING.md`.