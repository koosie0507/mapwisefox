VENV := .venv
TIMESTAMP := $(VENV)/.last_sync
PYTHON_VERSION := 3.13
PYTHON_PACKAGE_DIRS := deduplication kappa-score search search-judge snowballing split web/backend
PYTHON_TEST_DIRS := $(addsuffix /tests,$(PYTHON_PACKAGE_DIRS))
NODE_PACKAGE_DIRS := web/frontend
VALID_PACKAGES := $(PYTHON_PACKAGE_DIRS) $(NODE_PACKAGE_DIRS)
BUMP_KIND := $(or $(VERSION_COMPONENT),pre_label)

.PHONY: .check-deps bootstrap clean format check test

.check-deps:
	@command -v git >/dev/null 2>&1 || { echo "Error: 'git' is not installed or not in PATH." >&2; exit 1; }
	@command -v uv >/dev/null 2>&1 || { echo "Error: 'uv' is not installed or not in PATH." >&2; exit 1; }
	@command -v npm >/dev/null 2>&1 || { echo "Error: 'npm' is not installed or not in PATH" >&2; exit 1; }
	@command -v bump-my-version >/dev/null 2>&1 || { echo "Error: 'bump-my-version' is not installed or not in PATH." >&2; exit 1; }

$(VENV): | .check-deps
	@if [ ! -d "$(VENV)" ]; then \
		uv venv --python $(PYTHON_VERSION) $(VENV); \
	fi

$(TIMESTAMP): pyproject.toml uv.lock | $(VENV)
	uv sync --all-packages
	uv run python -c "from pathlib import Path; p=Path('$(TIMESTAMP)'); p.parent.mkdir(parents=True, exist_ok=True); p.touch()"

bootstrap: $(TIMESTAMP)

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
	uv tool run black $(PYTHON_PACKAGE_DIRS) --fast

check: bootstrap
	uv tool run black --check $(PYTHON_PACKAGE_DIRS)
	uv tool run ruff check $(PYTHON_PACKAGE_DIRS) --fix

PYTHON_EXISTING_TEST_DIRS := $(foreach d,$(PYTHON_TEST_DIRS),$(if $(wildcard $(d)),$(d),))
test: bootstrap
	uv run pytest -q $(PYTHON_EXISTING_TEST_DIRS)

.bump-version:
	@$(if $(PACKAGE),,$(error PACKAGE is required. Choose one of: $(VALID_PACKAGES)))
	@$(if $(filter $(PACKAGE),$(VALID_PACKAGES)),,$(error PACKAGE='$(PACKAGE)' is not one of: $(VALID_PACKAGES)))
	@$(info Using VERSION_COMPONENT='$(BUMP_KIND)')
	@VERSION_COMPONENT='$(BUMP_KIND)'; \
	echo "Bumping Python package $(PACKAGE) ($$VERSION_COMPONENT)"; \
	(cd "$(PACKAGE)" && uv tool run bump-my-version bump --dry-run -vv --no-tag "$$VERSION_COMPONENT")

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
