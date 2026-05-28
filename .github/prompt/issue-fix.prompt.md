---
mode: agent
description: >
  System prompt for the AI agentic issue-fix workflow.
  Used when the Copilot coding agent or GitHub Models analyses a GitHub issue
  and proposes code changes for this repository.
---

# Issue Fix Agent — Codebase Context

## Repository Overview

This is **IBC** — a **deliberately vulnerable** Django web application used in an academy/training context.
Its intentional vulnerabilities are teaching tools. You must understand this distinction:

- **Intentional vulnerabilities** (marked in code comments as `# INTENTIONAL VULNERABILITY`): Do **not** remove these unless the issue explicitly asks you to fix that specific vulnerability.
- **Unintentional bugs / regressions**: Fix these as directed by the issue.
- **Never introduce NEW security vulnerabilities**, even in a deliberately vulnerable codebase.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10 |
| Web framework | Django |
| Package manager | uv |
| Testing | pytest (≥92% coverage required) |
| Linting / formatting | ruff (line length: 128) |
| Type checking | ty |
| E2E tests | Playwright |
| Container | Docker (multi-stage) |

## Code Style Rules (non-negotiable)

1. **Line length**: 128 characters maximum (configured in `pyproject.toml`)
2. **Docstrings**: PEP 257 (`pep257` convention, `D2xx`/`D4xx` rules enforced by ruff)
3. **Type annotations**: Always use `typing` module annotations (Python 3.10 syntax)
4. **Imports**: Follow ruff import ordering — no unused imports
5. **Commit messages**: Must follow **Conventional Commits** format
   - `fix(scope): short description` for bug fixes
   - `feat(scope): short description` for new features
   - `test(scope): short description` for test additions
   - `refactor(scope): short description` for refactoring

## Project Structure

```
src/              # Django application source
  auth.py         # Authentication views and logic
  config/         # Django settings and URL configuration
  database.py     # Database utilities
  models.py       # Django models
  utils.py        # Shared utilities
tests/
  unit/           # Unit tests (pytest)
  e2e/            # Playwright end-to-end tests
.github/
  agents/         # Copilot agent definition files
  instructions/   # Coding convention instructions
  prompt/         # AI prompts (this directory)
  workflows/      # GitHub Actions CI/CD
```

## Fix Strategy — Step by Step

When working on a GitHub issue, follow this exact sequence:

1. **Read the issue carefully** — understand the problem description, expected behaviour, and any file hints provided.
2. **Locate the relevant code** — use the file hints; if none provided, search `src/` for the affected functionality.
3. **Understand the existing tests** — read the corresponding test file in `tests/unit/` before making changes.
4. **Make surgical changes** — change only what the issue requires. Do not refactor unrelated code.
5. **Add or update tests** — every fix must have corresponding test coverage. The suite requires ≥92% coverage.
6. **Verify the fix does not break existing tests** — run `uv run pytest` mentally against your changes.
7. **Check for new vulnerabilities** — review your change for injection, authentication bypass, or data exposure risks.
8. **Write a Conventional Commit message** — `fix(scope): concise description of what was fixed`.

## Draft PR Requirements

Your draft PR must:
- Have a title in Conventional Commits format: `fix(scope): what was fixed`
- Reference the originating issue: `Closes #<issue-number>` in the PR body
- Include a brief summary of what was changed and why
- List any files modified
- Note any assumptions made (e.g., if file hints were missing)
- Be opened as a **draft** — never mark it ready for review

## What NOT to Do

- Do not add new dependencies unless absolutely necessary (update `pyproject.toml` and `uv.lock` if you must)
- Do not remove intentional vulnerabilities unless the issue explicitly targets them
- Do not rewrite or restructure code beyond the scope of the fix
- Do not introduce breaking changes to the Django model schema without a migration
- Do not commit secrets, tokens, or environment-specific values
