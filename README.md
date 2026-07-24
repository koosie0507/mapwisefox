# MapwiseFox

MapwiseFox is a suite of tools for performing systematic literature reviews.

The package provides several utilities:

- [x] `search` - provide one search query and run it against multiple backends.
- [x] `deduplicate` - deduplicate search results stored across multiple files.
- [x] `split-workload` - partitions review workloads among multiple team members.
- [x] `snowball` - performs configurable-depth backward or forward snowballing
  based on an input set of primary studies.
- [x] `assistant` - runs include/exclude or quality assessment filters using LLMs.
- [x] `metrics` - implements various metrics for inter-rater agreement.
- [x] `web` - standardized web form that allows manually selecting large numbers
  of primary studies using customizable inclusion/exclusion criteria.

## Building

To prevent most portability issues, a `Dockerfile` is provided. To build the
MapwiseFox Docker image locally, either [Docker](https://www.docker.com) or another [OCI](https://opencontainers.org)
container manager (e.g. [Podman](https://podman.io)) is required. The instructions below
assume a Linux/MacOSX environment and a `docker` shell alias.

Download or clone this repository to a local directory which we're going to
call `$MWFDIR`.

```shell
$ cd $MWFDIR
$ docker build -t mwf .
$ docker build --target frontend-runtime -t mwf-frontend .
```

The result is a backend image containing all CLIs in the MapwiseFox suite and
a separate frontend image.

## Running

MapwiseFox uses standard Python tooling and `uv` to manage packages. Those
familiar can build and run all MapwiseFox tools locally.

The Docker image should be run with a volume mount for the local working
directory containing the data set of the systematic literature review. A good
choice for this local working directory is `$MWFDIR/data`, but anything that
can be mounted as a Docker volume with read-write access will work. For example,
here's how to run the `search` command and store data in `$MWFDIR/data`:

```shell
$ docker run -it -v "$MWFDIR/data:/opt/mapwisefox/data" mwf search -D ./data/search-test
```

To run the interactive web form, start both images on the same Docker network.

```shell
$ docker network create mapwisefox
$ docker run -d --rm --name backend --network mapwisefox -v "$MWFDIR/data:/opt/mapwisefox/data" mwf web
$ docker run --rm --network mapwisefox -e BACKEND_URL=http://backend:8000 -p "8000:80" mwf-frontend
```

### Environment Variables 

Some search backends (Web of Science, Elsevier, Springer) and all LLM backends
except local ones require API keys to access their APIs. These can be provided
in an environment file. Example `.env` file:

```dotenv
MWF_WEB_AUTH_ENABLED=False
MWF_SEARCH_CLARIVATE_API_KEY=# API key for accessing Web of Science APIs
MWF_SEARCH_ELSEVIER_API_KEY=# API key for accessing Scopus/ScienceDirect
MWF_SEARCH_SPRINGER_API_KEY=# API key for accessing SpringerLink APIs
# The assistant only supports one provider at a time
MWF_ASSISTANT_API_KEY=# your OpenAI, Anthropic, Google or AWS Bedrock API key
```

## Contributing

The code repository for this package is hosted on GitHub. E-mail the authors to
gain access and then head on to `CONTRIBUTING.md`.
