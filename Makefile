VENV := .venv
TIMESTAMP := $(VENV)/.last_sync
PYTHON_VERSION := 3.13
PYTHON_PACKAGE_DIRS := deduplication kappa-score search search-judge snowballing split web/backend

.PHONY: .check-deps bootstrap clean format check test

.check-deps:
	@command -v git >/dev/null 2>&1 || { echo "Error: 'git' is not installed or not in PATH." >&2; exit 1; }
	@command -v uv >/dev/null 2>&1 || { echo "Error: 'uv' is not installed or not in PATH." >&2; exit 1; }

$(VENV): .check-deps
	uv venv --python $(PYTHON_VERSION) $(VENV)

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
	uv tool run ruff check $(PYTHON_PACKAGE_DIRS)

test: check
	uv run pytest $(PYTHON_PACKAGE_DIRS)
