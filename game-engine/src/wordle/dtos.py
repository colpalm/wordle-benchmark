"""Data Transfer Objects for service layer return values."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GameTurnDto(BaseModel):
    """DTO for game turn data."""
    
    id: UUID
    game_id: UUID
    turn_number: int = Field(ge=1, le=6)
    guess: str = Field(min_length=5, max_length=5)
    reasoning: Optional[str] = None
    is_correct: bool
    letter_results: list[dict]  # Letter-by-letter feedback as JSONB
    created_at: datetime

    model_config = {"from_attributes": True}


class LLMInteractionDto(BaseModel):
    """DTO for LLM interaction data."""
    
    id: UUID
    game_id: UUID
    turn_number: int = Field(ge=1, le=6)
    prompt_text: str
    raw_response: str
    parse_success: bool
    parse_error_message: Optional[str] = None
    attempt_number: int = Field(ge=1)
    response_time_ms: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[Decimal] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvalidWordAttemptDto(BaseModel):
    """DTO for invalid word attempt data."""
    
    id: UUID
    game_id: UUID
    turn_number: int = Field(ge=1, le=6)
    attempted_word: str = Field(min_length=5, max_length=5)
    attempt_number: int = Field(ge=1)
    created_at: datetime

    model_config = {"from_attributes": True}


class GameDto(BaseModel):
    """DTO for game data with optional relationships."""
    
    # Core game data
    id: UUID
    model_name: str
    template_name: str
    parser_name: str
    target_word: str
    date: date
    status: str
    guesses_count: int = Field(ge=0, le=6)
    won: bool
    duration_seconds: float = Field(ge=0)
    total_invalid_attempts: int = Field(ge=0, default=0)
    golf_score: int = Field(ge=-3, le=4)  # Won in 1 = -3, lost = +4
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # Optional relationships (loaded on demand)
    turns: Optional[list[GameTurnDto]] = None
    llm_interactions: Optional[list[LLMInteractionDto]] = None
    invalid_attempts: Optional[list[InvalidWordAttemptDto]] = None

    model_config = {"from_attributes": True}


class LeaderboardStatsDto(BaseModel):
    """DTO for leaderboard statistics from database view."""
    
    model_name: str
    total_games: int
    wins: int
    win_rate: float  # Percentage 0-100
    avg_guesses: Optional[float] = None  # Only for won games
    total_golf_score: int
    first_game_date: date
    last_game_date: date

    model_config = {"from_attributes": True}