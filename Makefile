.PHONY: help install install-dev test test-all lint format clean build docs

help:
	@echo "pyadi-build - Makefile commands"
	@echo ""
	@echo "Available targets:"
	@echo "  install       - Install package"
	@echo "  install-dev   - Install package in development mode with dev dependencies"
	@echo "  test          - Run fast unit tests"
	@echo "  test-all      - Run all tests (all Python versions)"
	@echo "  lint          - Run code linters"
	@echo "  format        - Format code with black"
	@echo "  clean         - Remove build and test artifacts"
	@echo "  build         - Build distribution packages"
	@echo "  docs          - Build documentation (placeholder)"

install:
	pip install .

install-dev:
	pip install -e ".[dev]"

test:
	nox -s tests

test-all:
	nox

lint:
	nox -s lint

format:
	nox -s format

clean:
	nox -s clean
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

docs:
	@echo "Documentation build not yet implemented"

# Development helpers
.PHONY: check-deps setup-hooks

check-deps:
	@echo "Checking dependencies..."
	@command -v git >/dev/null 2>&1 || { echo "Git is required but not installed. Aborting." >&2; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }
	@echo "All required dependencies are installed."

setup-hooks:
	@echo "Setting up git hooks..."
	@echo "#!/bin/bash" > .git/hooks/pre-commit
	@echo "make lint" >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Git hooks installed."
