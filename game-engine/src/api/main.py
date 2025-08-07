"""FastAPI application for Wordle Benchmark frontend."""

from datetime import date
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import Game
from database.config import ApplicationConfig
from database.service import GameDatabaseService

# Create FastAPI app
app = FastAPI(
    title="Wordle Benchmark API",
    description="API for Wordle LLM performance visualization",
    version="0.1.0-dev",
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_db_service() -> GameDatabaseService:
    """Get a database service instance."""
    config = ApplicationConfig()
    return GameDatabaseService(config)


@app.get("/api/v1/games", response_model=list[Game])
async def get_games_by_date(
    date_param: Optional[str] = None,
    include_turns: bool = False,
    db_service: GameDatabaseService = Depends(get_db_service),  # noqa: B008
) -> list[Game]:
    """
    Get all games for a specific date.

    Args:
        date_param: Date in YYYY-MM-DD format
        include_turns: Include turn-by-turn game data (default: False)
        db_service: Database service instance

    Returns:
        List of games with optional turn information
    """
    print(f"DEBUG: date_param={date_param}, include_turns={include_turns} (type: {type(include_turns)})")
    try:
        if date_param:
            game_date = date.fromisoformat(date_param)
        else:
            # If no date specified, return empty list for now
            # TODO: Add method to get latest available date
            return []

        games = db_service.get_games_by_date(game_date, include_relationships=include_turns)
        return [Game.model_validate(game) for game in games]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
