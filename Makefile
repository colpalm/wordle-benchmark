# Wordle Benchmark Build System
# ================================

.PHONY: lint-backend test-backend-fast test-backend-full test-backend build-backend

# Backend targets
lint-backend:
	cd game-engine && uv run ruff format .
	cd game-engine && uv run ruff check --fix .

test-backend-fast:
	cd game-engine && uv run pytest -m "not api_calls" ./tests/

test-backend-full:
	cd game-engine && uv run pytest ./tests/

test-backend: test-backend-fast

build-backend: lint-backend test-backend-fast