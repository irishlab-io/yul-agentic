# Copilot Instructions — IBC

This is a **deliberately vulnerable** Django application used in an academy context.

## Commands

```bash
# Setup
uv venv .venv --python 3.14 && uv sync --all-extras --all-packages

# Run server
uv run python manage.py migrate && uv run python manage.py runserver

# Test (full suite — requires 92% coverage)
uv run pytest

# Run a single test file
uv run pytest tests/unit/test_views.py

# Run a single test by name
uv run pytest -k "test_login"

# Run only a specific marker
uv run pytest -m security
uv run pytest -m e2e   # requires: uv run playwright install --with-deps

# Lint / format (staged files only, excludes tests/)
uv run ruff check
uv run ruff format

# Type check (staged files only)
uv run ty check

# Django management
uv run python manage.py check
uv run python manage.py migrate
```

Tests run in parallel (`--numprocesses auto`) and require ≥92% coverage. E2E tests use Playwright; install browsers first with `uv run playwright install --with-deps`.

## Code style

Line length is **128** characters (configured in `pyproject.toml`). Ruff enforces PEP 257 docstrings (`pep257` convention, `D2xx`/`D4xx` rules). The `typing` module should be used for annotations; target is Python 3.10.

### Commits

Commit messages must follow **Conventional Commits** (`feat:`, `fix:`, `chore:`, etc.) — enforced by commitizen via pre-commit on the `commit-msg` hook.
