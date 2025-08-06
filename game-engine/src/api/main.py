"""FastAPI application for Wordle Benchmark frontend."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database.config import ApplicationConfig
from database.service import GameDatabaseService
from api.schemas import GameDetails, GameSummary


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


@app.get("/api/v1/games", response_model=list[GameSummary])
async def get_games_by_date(
    date_param: Optional[str] = None,
    db_service: GameDatabaseService = Depends(get_db_service)
) -> List[GameSummary]:
    """
    Get all games for a specific date.
    Returns basic game information without full turn details.
    """
    try:
        if date_param:
            game_date = date.fromisoformat(date_param)
        else:
            # If no date specified, return empty list for now
            # TODO: Add method to get latest available date
            return []
        
        games = db_service.get_games_by_date(game_date)
        return [GameSummary.model_validate(game) for game in games]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/api/v1/games/{game_id}", response_model=GameDetails)
async def get_game_details(
    game_id: UUID,
    db_service: GameDatabaseService = Depends(get_db_service)
) -> GameDetails:
    """
    Get full game details including turns, reasoning, and letter results.
    """
    try:
        game = db_service.get_game_by_id(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return GameDetails.model_validate(game)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)