"""Data Transfer Objects for service layer return values."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class InvalidWordAttemptDto(BaseModel):
    """DTO for invalid word attempt data."""

    id: UUID
    game_id: UUID
    turn_number: int = Field(ge=1, le=6)
    attempted_word: str = Field(min_length=5, max_length=5)
    attempt_number: int = Field(ge=1)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
    golf_score: int = Field(ge=-3, le=4)  # Golf Score: Won in 1 = -3, lost = +4
    created_at: datetime
    completed_at: Optional[datetime] = None

    # Optional relationships (loaded on demand)
    turns: Optional[list[GameTurnDto]] = None
    llm_interactions: Optional[list[LLMInteractionDto]] = None
    invalid_attempts: Optional[list[InvalidWordAttemptDto]] = None

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class RecentGameDto(BaseModel):
    """DTO for recent game result data."""

    game_date: date = Field(description="Game date")
    won: bool = Field(description="Whether the game was won or lost")

    model_config = ConfigDict(from_attributes=True)


class LeaderboardEntryDto(BaseModel):
    """DTO for single model entry in the leaderboard."""

    model_name: str = Field(description="LLM model identifier")
    total_games: int = Field(ge=0, description="Total number of games played")
    wins: int = Field(ge=0, description="Total number of games won")
    win_rate: float = Field(ge=0.0, le=100.0, description="Win percentage (0-100)")
    avg_guesses: Optional[float] = Field(ge=1.0, le=6.0, description="Average guesses for won games only")
    total_golf_score: int = Field(description="Total golf score (lower is better)")
    first_game_date: date = Field(description="Date of first game")
    last_game_date: date = Field(description="Date of most recent game")
    recent_form: list[RecentGameDto] = Field(default_factory=list, description="Last 5 games for recent form")

    model_config = ConfigDict(from_attributes=True)


class LeaderboardMetadataDto(BaseModel):
    """DTO for leaderboard response metadata."""

    total_games: int = Field(ge=0, description="Total games across all models")
    total_models: int = Field(ge=0, description="Number of models in leaderboard")
    last_updated: datetime = Field(description="Timestamp when data was last updated")

    model_config = ConfigDict(from_attributes=True)


class LeaderboardResponseDto(BaseModel):
    """DTO for complete leaderboard response."""

    leaderboard: list[LeaderboardEntryDto] = Field(description="List of model performance entries")
    metadata: LeaderboardMetadataDto = Field(description="Response metadata")

    model_config = ConfigDict(from_attributes=True)
