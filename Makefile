.PHONY: test test-py lint prompts web-build
test: test-py
test-py:
	PYTHONPATH=packages/config/src python -m pytest tests -q
# Phase 3 REAL-model exit gate (owner 2026-10-04 #12): BLOCKED conditions FAIL here.
materialize-models:
	PYTHONPATH=packages/config/src python scripts/materialize_models.py all
smoke-real:
	REQUIRE_REAL_MODELS=1 PYTHONPATH=packages/config/src python -m pytest tests/real_models -q
lint:
	ruff check .
prompts:
	python scripts/extract_prompts.py
web-build:
	cd apps/web && pnpm build
