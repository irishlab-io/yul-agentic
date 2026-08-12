# Copilot Instructions — vulnerable-todo-app

This is a **deliberately vulnerable Flask** TODO application used in a cybersecurity academy context. Its weaknesses are the curriculum, not defects. Never deploy it, and never "harden" it casually.

## Commands

Prefer the `Makefile` targets — they are the source of truth and mirror CI.

```bash
# Setup
make install          # uv venv + uv sync --all-extras --dev --frozen + playwright install

# Run server
make run              # uv run python run.py

# Test (full suite with coverage — mirrors CI, requires ≥75% coverage)
make test

# Faster loops
make test-unit        # uv run pytest -m unit
make test-fast        # uv run pytest -m "not slow" --numprocesses auto

# Run a single test file / a single test by name
uv run pytest tests/test_auth.py
uv run pytest -k "test_login"

# Lint / format / typecheck
make style            # format + lint + typecheck
make lint             # uv run ruff check --fix src
make format           # uv run ruff format src
make typecheck        # uv run ty check src

# Pre-commit
make pre-com-run      # prek run --all-files --color auto
```

Tests run in parallel (`--numprocesses auto`) over `src` and are gated at `--cov-fail-under=75`. Markers are `unit`, `integration`, and `slow`, with `--strict-markers` enabled — an undeclared marker fails the run. Note that ruff and the pytest pre-commit hooks exclude `tests/`, so run `make test` yourself.

## Layout

- `src/__init__.py` — `create_app()` and the HTTP routes
- `src/auth.py` — registration, login, session tokens, password change
- `src/database.py` — todo CRUD, search, sharing, file records
- `src/models.py` — the `Database` class and schema
- `src/utils.py` — hashing, subprocess, file I/O, pickle, HTTP fetch, XML parsing
- `src/feature_flags.py` + `feature_flags.yml` — YAML-backed feature flags
- `src/config/` — application configuration
- `web/templates/`, `web/static/` — Jinja templates and assets
- `run.py` — entrypoint
- `tests/test_*.py`, `tests/conftest.py` — test suite and shared fixtures

## Code style

Python `>=3.11`, managed with `uv` (`required-version >=0.11.18`). PEP 8 with **ruff's defaults** — there is no `[tool.ruff]` section in `pyproject.toml` and no `.ruff.toml`, so the line length is ruff's default of 88. PEP 257 docstrings. Use the `typing` module for annotations. Type checking is `ty`.

### Commits

Commit messages must follow **Conventional Commits** (`feat:`, `fix:`, `chore:`, etc.) — enforced by commitizen via pre-commit on the `commit-msg` hook.

## The vulnerabilities are intentional

`docs/VULNERABILITIES.md` catalogues 16 intentional weaknesses by CWE, with their exact code locations — SQL injection (CWE-89), XSS (CWE-79), CSRF (CWE-352), IDOR (CWE-639), path traversal (CWE-22), OS command injection (CWE-78), XXE (CWE-611), SSRF (CWE-918), insecure deserialization (CWE-502), hardcoded credentials (CWE-798), weak cryptography (CWE-327), information disclosure (CWE-200), missing authentication (CWE-306), unrestricted file upload (CWE-434), container security issues, and vulnerable dependencies. The pinned dependency versions in `pyproject.toml` carry known CVEs on purpose.

**Read `docs/VULNERABILITIES.md` before changing security-relevant code.** Removing or weakening a documented teaching vulnerability without being asked to destroys the exercise. Say so and stop rather than doing it silently.

Related docs: `docs/QUICKSTART.md`, `docs/TESTING.md`, `docs/EXPLOITS.md`.

---

## AI Agentic Workflows

This repository automates issue handling with [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/), using `engine: copilot`.

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `.github/workflows/aw-triage.md` | Issue opened/reopened, or `workflow_dispatch` | Classifies the issue, applies category and `severity:*` labels, posts one guidance comment |
| `.github/workflows/aw-fixer.md` | `enhancement` or `security` label applied, or `workflow_dispatch` | Implements the fix and opens a draft PR on an `ai/`-prefixed branch |

Each workflow delegates its real work to a sub-agent in `.github/agents/`:

| Agent | Role |
|-------|------|
| `triage-analyst.agent.md` | Owns the category taxonomy, severity scale, intentional-vulnerability rules, and reporter-facing comment guidance |
| `software-engineer.agent.md` | Owns codebase grounding, the fix-to-PR procedure, the PR quality bar, and security-remediation rules |
| `security-reviewer.agent.md` | Reviews diffs, separating intentional vulnerabilities from unintended weaknesses and curriculum damage |

The `security-reviewer` is also invocable directly from Copilot CLI or VS Code for ad-hoc reviews.

Workflows are compiled to `.lock.yml` files with `gh aw compile`; never edit a `.lock.yml` by hand.

### Reviewing AI-generated PRs

All AI-generated PRs open as **drafts**, labelled `agentic-workflow` + `needs-review`. Before merging:

1. Read every changed line — do not assume the agent is correct
2. Run `make test` to verify no regressions and that coverage holds at ≥75%
3. Check that no intentional vulnerability was accidentally removed (`docs/VULNERABILITIES.md`)
4. Mark the PR **Ready for Review** and merge only after CI passes and a human approves
