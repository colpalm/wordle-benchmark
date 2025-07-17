from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from wordle.enums import LetterStatus, GameStatus
import uuid


## Database-aligned Pydantic models for SQLAlchemy entities ##

class Game(BaseModel):
    """Pydantic model matching Game SQLAlchemy table."""
    id: Optional[uuid.UUID] = None
    model_name: str = Field(max_length=100)
    template_name: str = Field(max_length=20)
    parser_name: str = Field(max_length=20)
    target_word: str = Field(min_length=5, max_length=5)
    date: date
    status: str = Field(max_length=20)  # "won", "lost"
    guesses_count: int = Field(ge=0, le=6)
    won: bool
    duration_seconds: float = Field(ge=0)
    total_invalid_attempts: int = Field(ge=0, default=0)
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class GameTurn(BaseModel):
    """Pydantic model matching GameTurn SQLAlchemy table."""
    id: Optional[uuid.UUID] = None
    game_id: uuid.UUID
    turn_number: int = Field(ge=1, le=6)
    guess: str = Field(min_length=5, max_length=5)
    reasoning: Optional[str] = None
    is_correct: bool
    letter_results: List[dict]  # Letter-by-letter feedback
    created_at: Optional[datetime] = None


class LLMInteraction(BaseModel):
    """Pydantic model matching LLMInteraction SQLAlchemy table."""
    id: Optional[uuid.UUID] = None
    game_id: uuid.UUID
    turn_number: int = Field(ge=1, le=6)
    prompt_text: str
    raw_response: str
    parse_success: bool
    parse_error_message: Optional[str] = None
    attempt_number: int = Field(ge=1)
    response_time_ms: Optional[int] = None

    # Usage tracking fields
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[Decimal] = None

    created_at: Optional[datetime] = None


class InvalidWordAttempt(BaseModel):
    """Pydantic model matching InvalidWordAttempt SQLAlchemy table."""
    id: Optional[uuid.UUID] = None
    game_id: uuid.UUID
    turn_number: int = Field(ge=1, le=6)
    attempted_word: str = Field(min_length=5, max_length=5)
    attempt_number: int = Field(ge=1)
    created_at: Optional[datetime] = None


class GameUsageSummary(BaseModel):
    """Pydantic model matching GameUsageSummary SQLAlchemy view."""
    game_id: uuid.UUID
    total_tokens_input: Optional[int] = None
    total_tokens_output: Optional[int] = None
    total_tokens_reasoning: Optional[int] = None
    total_tokens_all: Optional[int] = None
    cost_usd: Optional[Decimal] = None
    response_time_avg_ms: Optional[float] = None
    total_requests: int


## Runtime Pydantic models ##


class LetterResult(BaseModel):
    position: int = Field(ge=0, le=4)
    letter: str = Field(min_length=1, max_length=1)
    status: LetterStatus


class GameState(BaseModel):
    target_word: str = Field(min_length=5, max_length=5)
    guesses: List[str] = Field(default_factory=list)
    guess_reasoning: List[Optional[str]] = Field(default_factory=list)
    guess_results: List[List[LetterResult]] = Field(default_factory=list)
    guesses_made: int = Field(ge=0, le=6)
    guesses_remaining: int = Field(ge=0, le=6)
    status: GameStatus
    won: bool
    game_over: bool


class UsageStats(BaseModel):
    total_requests: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_tokens_reasoning: int = 0
    total_cost_usd: float = 0.0
    response_time_avg_ms: float = 0.0


class GameMetadata(BaseModel):
    model: str
    template: str
    parser: str
    duration_seconds: float = Field(ge=0)
    start_time: datetime
    end_time: datetime
    date: str  # YYYY-MM-DD format
    invalid_word_attempts: List[str] = Field(default_factory=list)
    total_invalid_attempts: int = Field(ge=0, default=0)


class GameResult(BaseModel):
    success: bool
    game_state: Optional[GameState] = None
    metadata: GameMetadata
    error: Optional[str] = None
    
    # Convenience properties
    @property
    def won(self) -> bool:
        return self.game_state.won if self.game_state else False
    
    @property
    def target_word(self) -> str:
        return self.game_state.target_word if self.game_state else None
    
    @property
    def guesses_made(self) -> int:
        return self.game_state.guesses_made if self.game_state else 0