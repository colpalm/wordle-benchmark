from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from wordle.enums import LetterStatus, GameStatus


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
    usage_stats: Optional[UsageStats] = None


class GameResult(BaseModel):
    success: bool
    game_state: GameState
    metadata: GameMetadata
    error: Optional[str] = None
    
    # Convenience properties
    @property
    def won(self) -> bool:
        return self.game_state.won
    
    @property
    def target_word(self) -> str:
        return self.game_state.target_word
    
    @property
    def guesses_made(self) -> int:
        return self.game_state.guesses_made