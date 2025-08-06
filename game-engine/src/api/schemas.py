"""Pydantic schemas for API responses."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from wordle.enums import LetterStatus


class LetterResult(BaseModel):
    """Letter result in Wordle game."""
    position: int
    letter: str
    status: LetterStatus


class GameTurn(BaseModel):
    """Individual turn in a Wordle game."""
    id: UUID
    turn_number: int
    guess: str
    reasoning: Optional[str]
    is_correct: bool
    letter_results: list[dict]  # Keep as dict for now, matches database JSONB
    created_at: datetime

    class Config:
        from_attributes = True


class GameSummary(BaseModel):
    """Basic game information for list views."""
    id: UUID
    model_name: str
    template_name: str
    parser_name: str
    target_word: str
    date: date
    status: str
    guesses_count: int
    won: bool
    duration_seconds: float
    total_invalid_attempts: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class GameDetails(GameSummary):
    """Full game details including turns."""
    turns: list[GameTurn]
    # Note: Excluding llm_interactions and invalid_attempts for now
    # to keep the API response simpler. Can add them later if needed.

    class Config:
        from_attributes = True