# wordle-benchmark
Testing LLM performance with Wordle

## Quick Start

### Docker Deployment (Recommended)

1. **Setup Environment:** Copy and configure your environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your OPENROUTER_API_KEY and other settings
   ```

2. **Build the Project:** Run the full build process (lint, test, and build Docker images):
   ```bash
   make dev
   ```

3. **Deploy Services:** Start all services (PostgreSQL + game-engine + frontend):
   ```bash
   make docker-up
   ```
   
   Access the application:
   - **Frontend:** http://localhost:3000
   - **Backend API:** http://localhost:8000
   
4. **Run Wordle Game** - Kick off a sequence of Wordle Games
   ```bash
   docker compose exec game-engine uv run python -m wordle.game_runner 
   ```

5. **Stop Services:**
   ```bash
   make docker-down   # Stop containers
   make docker-clean  # Stop containers and remove volumes (full reset)
   ```

## Development Workflows

### Option 1: Full Docker (Production-like Testing)
Use this when you want to test the complete containerized application:

```bash
make dev         # Build all images
make docker-up   # Start all services
```

### Option 2: Hybrid Development (Frontend Development)
Use this when making frontend changes and need hot reloading:

```bash
make docker-frontend-dev-up    # Start backend in Docker + frontend locally
# Frontend available at http://localhost:3000 with hot reload
# Backend API available at http://localhost:8000

make docker-frontend-dev-down  # Stop all services
```

**Benefits of hybrid approach:**
- Fast frontend development with hot reloading
- Backend services isolated in Docker
- No need to rebuild Docker images for frontend changes

### Available Commands

- `make help` - Show all available targets
