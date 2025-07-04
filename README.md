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

Either [Docker](https://www.docker.com) or another
[OCI](https://opencontainers.org) container manager
(e.g. [Podman](https://podman.io)) must be installed.
At least a `docker` shell alias is required for the instructions below to work.

Then you must create a `.env`

```shell
# set UPLOADS_DIR to a path where you store the Excel files containing primary studies
$ docker build -t ersa .
$ docker run -it -p 8000:8000 -v "$UPLOADS_DIR:/app/uploads" ersa web
```

## Contributing

The code repository for this package is hosted on GitHub. E-mail the authors to
gain access and then head on to `CONTRIBUTING.md`.