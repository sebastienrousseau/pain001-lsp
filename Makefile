.PHONY: help install dev test lint format type-check security clean examples doc-coverage check

# Mutation score floor for the language-server handlers: 87.9% (775 of
# 882) on 2026-09-18, up from 76.5% before the diagnostic-shape tests. The
# floor sits under it so one flaky mutant cannot block a release. Raise it
# when the score rises; never lower it to make a red run green.
MUTATION_FLOOR ?= 85

PYTHON ?= python3
POETRY ?= poetry

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(POETRY) install --only main

dev: ## Install all dependencies (including dev)
	$(POETRY) install

test: ## Run tests with the 100% line+branch coverage gate
	$(POETRY) run pytest tests/ \
		--cov=pain001_lsp --cov-branch \
		--cov-report=term-missing --cov-fail-under=100 -v

lint: ## Run linters (ruff + black check)
	$(POETRY) run ruff check pain001_lsp/ tests/
	$(POETRY) run black --check pain001_lsp/ tests/

format: ## Auto-format code (ruff fix + black)
	$(POETRY) run ruff check --fix pain001_lsp/ tests/
	$(POETRY) run black pain001_lsp/ tests/

type-check: ## Run mypy type checking
	$(POETRY) run mypy pain001_lsp/

security: ## Run security scan (bandit)
	$(POETRY) run bandit -r pain001_lsp/ -ll

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .eggs/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/
	rm -rf coverage.xml .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true

examples: ## Verify example scripts run
	$(POETRY) run python examples/01_lsp_helpers.py
	$(POETRY) run python examples/02_quick_fix.py
	$(POETRY) run python examples/03_configure_message_type.py
	$(POETRY) run python examples/04_corpus_commands.py

doc-coverage: ## Enforce the 100% docstring coverage gate
	$(POETRY) run interrogate -c pyproject.toml -v pain001_lsp

mutate: ## Mutation testing over the handlers (mutmut 3, config in pyproject)
	rm -rf mutants
	$(POETRY) run mutmut run
	$(POETRY) run mutmut export-cicd-stats
	$(POETRY) run python scripts/mutation_gate.py --floor $(MUTATION_FLOOR)

check: lint type-check security test doc-coverage examples ## Run all gates
