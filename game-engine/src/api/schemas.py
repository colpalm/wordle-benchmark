"""Pydantic schemas for API responses."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)


class Game(BaseModel):
    """Game model with optional relationships."""

    # Core game data (always present)
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
    golf_score: int
    created_at: datetime
    completed_at: Optional[datetime]

    # Optional relationships (populated based on query parameters)
    turns: Optional[list[GameTurn]] = None
    # Note: llm_interactions and invalid_attempts can be added later when needed

    model_config = ConfigDict(from_attributes=True)
