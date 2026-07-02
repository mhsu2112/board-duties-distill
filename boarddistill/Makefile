.PHONY: check lint typecheck test fmt sync cov schema

# The gate. Every task must end green here.
check: lint typecheck test

sync:
	uv sync

lint:
	uv run ruff check .

fmt:
	uv run ruff format .

typecheck:
	uv run mypy

test:
	uv run pytest

cov:
	uv run pytest --cov --cov-report=term-missing

# Export canonical JSON Schema (wired at T1).
schema:
	uv run python -m distillcore.export_schema
