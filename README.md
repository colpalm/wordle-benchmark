# wordle-benchmark
Testing LLM performance with Wordle

## Quick Start

### Docker Deployment (Recommended)

1. **Setup Environment:** Copy and configure your environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your OPENROUTER_API_KEY and other settings
   ```

2. **Build the Project:** Run the full build process (lint, test, and build Docker image):
   ```bash
   make build-backend
   ```

3. **Deploy Services:** Start all services (PostgreSQL + game-engine):
   ```bash
   make docker-up
   ```
   
4. **Run Wordle Game** - Kick off a sequence of Wordle Games
```bash
docker compose exec game-engine uv run python -m wordle.game_runner 
```

5. **Stop Services:**
   ```bash
   make docker-down   # Stop containers
   make docker-clean  # Stop containers and remove volumes (full reset)
   ```

### Available Commands

- `make help` - Show all available targets
