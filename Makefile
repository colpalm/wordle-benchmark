# Wordle Benchmark Build System
# ================================

# Get version from pyproject.toml to use as the default Docker image tag
VERSION := $(shell grep '^version' game-engine/pyproject.toml | sed 's/version = "\(.*\)"/\1/')
export VERSION

.PHONY: lint-backend lint-backend-fix lint-frontend lint-frontend-fix \
		test-backend-fast test-backend-full test-backend \
		docker-build docker-build-game-engine docker-build-frontend \
		docker-up docker-down docker-frontend-dev-up docker-frontend-dev-down docker-clean \
		dev ci help

# Help target
help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  lint-backend             Check backend formatting and linting"
	@echo "  lint-backend-fix         Format and lint backend code (auto-fix)"
	@echo "  lint-frontend            Check frontend formatting and linting"
	@echo "  lint-frontend-fix        Format and lint frontend code (auto-fix)"
	@echo "  test-backend-fast        Run backend tests (no API calls)"
	@echo "  test-backend-full        Run all backend tests including API calls"
	@echo "  test-backend             Alias for test-backend-fast"
	@echo "  docker-build             Build all Docker images"
	@echo "  docker-build-game-engine Build game-engine docker image"
	@echo "  docker-build-frontend    Build frontend docker image"
	@echo "  docker-up                Start all services using Docker Compose"
	@echo "  docker-down              Stop all services"
	@echo "  docker-clean             Stop all services and remove volumes"
	@echo "  docker-frontend-dev-up   Start backend services + local frontend dev"
	@echo "  docker-frontend-dev-down Stop backend services and frontend dev"
	@echo "  dev                      Development mode: auto-fix linting for backend and frontend"
	@echo "  ci                       Full CI pipeline (full build): verify backend, verify frontend, build images"

# Development mode (auto-fix)
dev: lint-backend-fix test-backend-fast lint-frontend-fix docker-build

# Main CI pipeline (full build)
ci: lint-backend test-backend-fast lint-frontend docker-build


# Backend targets
lint-backend:
	cd game-engine && uv run ruff format --check .
	cd game-engine && uv run ruff check .

lint-backend-fix:
	cd game-engine && uv run ruff format .
	cd game-engine && uv run ruff check --fix .

test-backend-fast:
	cd game-engine && uv run pytest -m "not api_calls" ./tests/

test-backend-full:
	cd game-engine && uv run pytest ./tests/

test-backend: test-backend-fast

# Frontend targets
lint-frontend:
	cd frontend && npm run format:check
	cd frontend && npm run lint

lint-frontend-fix:
	cd frontend && npm run format
	cd frontend && npm run lint

# Docker targets

docker-build: docker-build-game-engine docker-build-frontend

docker-build-game-engine:
	@echo "Syncing dependencies..."
	cd game-engine && uv sync
	@echo "Building Docker image with tag: wordle-benchmark/game-engine:$(VERSION)..."
	docker build -t wordle-benchmark/game-engine:$(VERSION) -f docker/game-engine/Dockerfile .

docker-build-frontend:
	@echo "Syncing dependencies..."
	cd frontend && npm install --package-lock-only
	@echo "Building Docker image with tag: wordle-benchmark/frontend:$(VERSION)..."
	docker build -t wordle-benchmark/frontend:$(VERSION) -f docker/frontend/Dockerfile .

docker-up:
	@echo "Starting all services..."
	@docker compose up

docker-down:
	@echo "Stopping all Docker Compose services..."
	@docker compose down

docker-clean:
	@echo "Stopping all Docker Compose services and removing volumes..."
	@docker compose down -v

docker-frontend-dev-up:
	@echo "Starting backend services with Docker Compose..."
	@docker compose up -d db game-engine
	@echo "Starting frontend development server..."
	@echo "Frontend will be available at http://localhost:3000"
	@echo "Backend API will be available at http://localhost:8000"
	@cd frontend && npm run dev

docker-frontend-dev-down:
	@echo "Stopping backend services..."
	@docker compose down