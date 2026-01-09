.PHONY: help install test lint format typecheck clean sync

help:
	@echo "Available commands:"
	@echo "  make install    - Create venv and install dependencies"
	@echo "  make sync       - Sync dependencies (after updating requirements)"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter"
	@echo "  make format     - Format code"
	@echo "  make typecheck  - Run type checker"
	@echo "  make clean      - Remove build artifacts"

install:
	uv venv
	uv pip install -r requirements-dev.txt
	uv pip install -e .

sync:
	uv pip sync requirements-dev.txt
	uv pip install -e .

test:
	pytest

lint:
	ruff check boxnotes tests

format:
	black boxnotes tests

typecheck:
	mypy boxnotes

clean:
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache .venv
