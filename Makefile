VENV := .venv
WEB_FRONTEND_DIR := web/frontend
NODE_MODULES := $(WEB_FRONTEND_DIR)/node_modules
NODE_TIMESTAMP := $(NODE_MODULES)/.package-lock.json
TIMESTAMP := $(VENV)/.last_sync
PYTHON_VERSION := 3.13
PYTHON_PACKAGE_DIRS := assistant common-config deduplication metrics search snowballing split web/backend
PYTHON_TEST_DIRS := $(addsuffix /tests,$(PYTHON_PACKAGE_DIRS))
VALID_PACKAGES := $(PYTHON_PACKAGE_DIRS) $(WEB_FRONTEND_DIR)
BUMP_KIND := $(or $(VERSION_COMPONENT),pre_label)

.PHONY: .check-deps bootstrap clean format check test \
       build-docs serve-docs prepare-pages clean-docs

.check-deps:
	@command -v git >/dev/null 2>&1 || { echo "Error: 'git' is not installed or not in PATH." >&2; exit 1; }
	@command -v uv >/dev/null 2>&1 || { echo "Error: 'uv' is not installed or not in PATH." >&2; exit 1; }
	@command -v npm >/dev/null 2>&1 || { echo "Error: 'npm' is not installed or not in PATH" >&2; exit 1; }

$(VENV): | .check-deps
	@if [ ! -d "$(VENV)" ]; then \
		uv venv --python $(PYTHON_VERSION) $(VENV); \
	fi

$(NODE_MODULES): | .check-deps
	@if [ ! -d "$(NODE_MODULES)" ]; then \
		cd $(WEB_FRONTEND_DIR) && npm install; \
	fi


$(TIMESTAMP): pyproject.toml uv.lock | $(VENV)
	uv sync --all-packages --active
	uv run python -c "from pathlib import Path; p=Path('$(TIMESTAMP)'); p.parent.mkdir(parents=True, exist_ok=True); p.touch()"

$(NODE_TIMESTAMP): $(WEB_FRONTEND_DIR)/package.json | $(NODE_MODULES)
	cd $(WEB_FRONTEND_DIR) && npm install

bootstrap: $(TIMESTAMP) $(NODE_TIMESTAMP)

clean:
	@# Remove .venv cross-platform (prefer Python if available, fallback to rm)
	@if command -v python3 >/dev/null 2>&1; then \
		python3 -c "import shutil; shutil.rmtree('.venv', ignore_errors=True)"; \
	elif command -v py >/dev/null 2>&1; then \
		py -3 -c "import shutil; shutil.rmtree('.venv', ignore_errors=True)"; \
	elif command -v python >/dev/null 2>&1; then \
		python -c "import shutil; shutil.rmtree('.venv', ignore_errors=True)"; \
	else \
		rm -rf .venv; \
	fi
	@# Clean untracked files but keep .venv if present
	git clean -fdx -e .venv

format: bootstrap
	uv run --active black $(PYTHON_PACKAGE_DIRS)
	uv run --active ruff check --fix $(PYTHON_PACKAGE_DIRS)
	cd $(WEB_FRONTEND_DIR) && npm run lint -- --fix

check: bootstrap
	uv run --active black --check --diff $(PYTHON_PACKAGE_DIRS)
	uv run --active ruff check $(PYTHON_PACKAGE_DIRS)
	cd $(WEB_FRONTEND_DIR) && npm run lint

PYTHON_EXISTING_TEST_DIRS := $(foreach d,$(PYTHON_TEST_DIRS),$(if $(wildcard $(d)),$(d),))
test: bootstrap
	uv run --active pytest -rA -vvs --log-level INFO \
		--junitxml=.test-reports/backend/results.xml \
		--cov=mapwisefox \
		--cov-branch \
		--cov-report=xml:.test-reports/backend/coverage.xml \
		--cov-report=term-missing \
		$(PYTHON_EXISTING_TEST_DIRS)
	cd $(WEB_FRONTEND_DIR) && npm run test:coverage

.bump-version:
	@$(if $(PACKAGE),$(if $(filter $(PACKAGE),$(VALID_PACKAGES)),,$(error PACKAGE='$(PACKAGE)' is not one of: $(VALID_PACKAGES))),)
	@$(if $(PACKAGE),$(info Using PACKAGE='$(PACKAGE)'),$(info PACKAGE not set; bumping workspace root))
	@$(info VERSION_COMPONENT='$(BUMP_KIND)')
	@VERSION_COMPONENT='$(BUMP_KIND)'; \
	echo "Bumping Python package $(PACKAGE) ($$VERSION_COMPONENT)"; \
	if [ -n "$(PACKAGE)" ]; then cd "$(PACKAGE)"; fi; \
	uv tool run bump-my-version bump --no-tag "$$VERSION_COMPONENT"

bump-major: BUMP_KIND=major
bump-major: .bump-version

bump-minor: BUMP_KIND=minor
bump-minor: .bump-version

bump-patch: BUMP_KIND=patch
bump-patch: .bump-version

bump-prerelease: BUMP_KIND=pre_number
bump-prerelease: .bump-version

bump-release: BUMP_KIND=pre_label
bump-release: .bump-version

new-tag: .check-deps
	@VERSION=$$(uv tool run bump-my-version show current_version); \
	git tag -a "v$$VERSION" -m "Version $$VERSION" && \
	git push --tags && echo "Pushed tag v$$VERSION" || echo "Failed to push tag v$$VERSION"

re-tag: .check-deps
	@$(if $(TAG),,$(error 're-tagging requires specifying a TAG'))
	git push --delete origin refs/tags/$(TAG) && \
	git tag --delete $(TAG) && \
	git tag $(TAG) && \
	git push --tags

# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------
# build-docs: strict local build for verification (output in ./_site).
# serve-docs: local dev server with live reload (single version).
# prepare-pages: deploy current checkout to gh-pages as VERSION + 'latest' alias.
#   Requires VERSION, e.g. `make prepare-pages VERSION=v0.9.6`. Pushes to origin.
# clean-docs: remove local build output.
#
# Docs targets sync only the `docs` dependency group (mkdocs-material,
# mkdocstrings, include-markdown, mike) rather than the full workspace.

build-docs:
	uv sync --only-group docs --active
	uv run --active mkdocs build --strict --site-dir _site

serve-docs:
	uv sync --only-group docs --active
	uv run --active mkdocs serve --strict

prepare-pages:
	@test -n "$(VERSION)" || { echo "VERSION required (e.g. make prepare-pages VERSION=v0.9.6)"; exit 1; }
	uv sync --only-group docs --active
	uv run --active mike deploy --update-aliases --push "$(VERSION)" latest
	uv run --active mike set-default latest --push

clean-docs:
	rm -rf _site
