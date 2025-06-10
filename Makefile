.PHONY: help install install-dev test lint format type-check security-check pre-commit clean build docs

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install package in development mode"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  test         - Run tests with coverage"
	@echo "  test-fast    - Run tests without coverage"
	@echo "  lint         - Run ruff linting"
	@echo "  format       - Format code with ruff and black"
	@echo "  type-check   - Run mypy type checking"
	@echo "  security-check - Run bandit security checks"
	@echo "  pre-commit   - Run pre-commit hooks on all files"
	@echo "  quality      - Run all quality checks (lint, format, type-check, security)"
	@echo "  clean        - Clean build artifacts and cache"
	@echo "  build        - Build package"
	@echo "  docs         - Generate documentation"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

# Testing targets
test:
	pytest --cov=. --cov-report=term-missing --cov-report=html:test_output/htmlcov

test-fast:
	pytest -x -v

test-integration:
	pytest -m integration

test-unit:
	pytest -m unit

# Code quality targets
lint:
	ruff check .

format:
	ruff format .
	ruff check . --fix

type-check:
	mypy .

security-check:
	bandit -r . -f json -o test_output/bandit-report.json || true
	bandit -r . --severity-level medium

# Combined quality check
quality: lint type-check security-check
	@echo "✅ All quality checks passed!"

# Pre-commit
pre-commit:
	pre-commit run --all-files

# Maintenance targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf test_output/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

# Development workflow
dev-setup: install-dev
	@echo "🚀 Development environment setup complete!"
	@echo "Run 'make test' to verify everything works"

# CI simulation
ci: quality test
	@echo "🎉 CI checks passed!"

# Documentation (placeholder for future)
docs:
	@echo "📚 Documentation generation not yet implemented"
	@echo "Consider adding sphinx or mkdocs in the future"
