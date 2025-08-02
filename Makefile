# Wordle Benchmark Build System
# ================================

# Get version from pyproject.toml to use as the default Docker image tag
VERSION := $(shell grep '^version' game-engine/pyproject.toml | sed 's/version = "\(.*\)"/\1/')
export VERSION

.PHONY: lint-backend test-backend-fast test-backend-full test-backend build-backend docker-build docker-up docker-down docker-clean help

# Backend targets
lint-backend:
	cd game-engine && uv run ruff format .
	cd game-engine && uv run ruff check --fix .

test-backend-fast:
	cd game-engine && uv run pytest -m "not api_calls" ./tests/

test-backend-full:
	cd game-engine && uv run pytest ./tests/

test-backend: test-backend-fast

build-backend: lint-backend test-backend-fast docker-build

# Docker targets
help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  lint-backend      Format and lint backend code"
	@echo "  test-backend-fast Run backend tests (no API calls)"
	@echo "  test-backend-full Run all backend tests including API calls"
	@echo "  build-backend     Lint, test, and build Docker image for backend"
	@echo "  docker-build      Build the game-engine Docker image"
	@echo "  docker-up         Start all services using Docker Compose"
	@echo "  docker-down       Stop all services"
	@echo "  docker-clean      Stop all services and remove volumes"

docker-build:
	@echo "Syncing dependencies..."
	cd game-engine && uv sync
	@echo "Building Docker image with tag: wordle-benchmark/game-engine:$(VERSION)..."
	docker build -t wordle-benchmark/game-engine:$(VERSION) -f docker/game-engine/Dockerfile .

docker-up:
	@echo "Starting all services..."
	@docker compose up

docker-down:
	@echo "Stopping all Docker Compose services..."
	@docker compose down

docker-clean:
	@echo "Stopping all Docker Compose services and removing volumes..."
	@docker compose down -v