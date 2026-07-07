.DEFAULT_GOAL := help
.PHONY: check clean clean-cache clean-coverage docker-build docker-down docker-logs docker-up format help install install-dev lint pre-commit pre-commit-all pre-commit-install run setup style test test-fast test-integration test-unit typecheck


PYTHON_VERSION := 3.11
PRE_COM := prek
UV := uv
VENV := .venv
SRC := src
TESTS := tests

# ──────────────────────────────────────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────────────────────────────────────

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
	     /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 } \
	     /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

# ──────────────────────────────────────────────────────────────────────────────
##@ Setup
# ──────────────────────────────────────────────────────────────────────────────

setup: pre-com-setup load-env ## Bootstrap project

install: ## Install all dependencies (main + dev) via uv
	$(UV) venv .venv --clear
	$(UV) sync --all-extras --dev --frozen
	$(UV) run playwright install --with-deps

pre-com-setup: ## Install pre-commit hooks into .git
	$(UV) tool install pre-commit
	$(PRE_COM) install --allow-missing-config

load-env: ## Copy .env.sample → .env if .env does not exist yet, then source it
	@if [ -f .env ]; then \
		echo ".env already exists, skipping copy"; \
	elif [ -f .env.sample ]; then \
		cp .env.sample .env && echo "Created .env from .env.sample"; \
	else \
		echo "No .env.sample found, skipping"; \
	fi

# ──────────────────────────────────────────────────────────────────────────────
##@ Quality
# ──────────────────────────────────────────────────────────────────────────────

pre-com-run: ## Run pre-commit on all files
	$(PRE_COM) run --all-files --color auto

style: format lint typecheck ## Run all style checks (format, lint, typecheck)

lint: ## Lint source with ruff-check (auto-fix enabled)
	$(UV) run ruff check --fix $(SRC)

format: ## Format source with ruff-format
	$(UV) run ruff format $(SRC)

typecheck: ## Type-check source with ty
	$(UV) run ty check $(SRC)

# ──────────────────────────────────────────────────────────────────────────────
##@ Testing
# ──────────────────────────────────────────────────────────────────────────────

test: ## Run full test suite with coverage (mirrors CI)
	$(UV) run pytest

test-fast: ## Run tests skipping slow markers, parallel
	$(UV) run pytest -m "not slow" --numprocesses auto

test-unit: ## Run only unit-marked tests
	$(UV) run pytest -m unit

test-integration: ## Run only integration-marked tests
	$(UV) run pytest -m integration

test-watch: ## Re-run tests on file changes (requires pytest-watch)
	$(UV) run ptw -- --tb=short

# ──────────────────────────────────────────────────────────────────────────────
##@ Run
# ──────────────────────────────────────────────────────────────────────────────

run: ## Start the Flask development server
	$(UV) run python run.py

# ──────────────────────────────────────────────────────────────────────────────
##@ Docker
# ──────────────────────────────────────────────────────────────────────────────

docker-build: ## Build the Docker image
	docker build -t vulnerable-todo-app:local .

docker-up: ## Start services with Docker Compose
	docker compose up --build -d

docker-down: ## Stop and remove Docker Compose services
	docker compose down

docker-logs: ## Tail logs from Docker Compose services
	docker compose logs -f

# ──────────────────────────────────────────────────────────────────────────────
##@ Maintenance
# ──────────────────────────────────────────────────────────────────────────────

deps-update: ## Update uv.lock to latest compatible versions
	$(UV) lock --upgrade

deps-export: ## Regenerate requirements.txt from uv.lock
	$(UV) export --no-hashes --output-file requirements.txt

clean: clean-cache clean-coverage ## Remove caches and coverage artifacts
	rm -rf $(VENV)

clean-cache: ## Remove Python bytecode and pytest/ruff caches
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
	find . -type f -name '*.pyc' -not -path './.venv/*' -delete
	rm -rf .pytest_cache .ruff_cache

clean-coverage: ## Remove coverage reports
	rm -rf htmlcov $(TESTS)/coverage coverage.xml .coverage
