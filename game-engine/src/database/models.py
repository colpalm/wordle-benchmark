"""SQLAlchemy database models for Wordle benchmark system."""

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Date, Index, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import date, datetime
import uuid


# Constants
CASCADE_RULES = "all, delete-orphan"
GAME_ID_FK = "games.id"


class Base(DeclarativeBase):
    pass


class Game(Base):
    """Core game data for fast queries and leaderboards."""
    __tablename__ = 'games'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(100))
    template_name: Mapped[str] = mapped_column(String(20))  # "simple", "json"
    parser_name: Mapped[str] = mapped_column(String(20))    # "simple", "json"
    target_word: Mapped[str] = mapped_column(String(5))
    date: Mapped[date] = mapped_column(Date)                # Wordle puzzle date
    status: Mapped[str] = mapped_column(String(20))         # "won", "lost"
    guesses_count: Mapped[int] = mapped_column(Integer)
    won: Mapped[bool] = mapped_column(Boolean)
    duration_seconds: Mapped[float] = mapped_column(Float)
    total_invalid_attempts: Mapped[int] = mapped_column(Integer, default=0)
    game_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)  # API costs, tokens, performance
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    turns: Mapped[List["GameTurn"]] = relationship(back_populates="game", cascade=CASCADE_RULES)
    llm_interactions: Mapped[List["LLMInteraction"]] = relationship(back_populates="game", cascade=CASCADE_RULES)
    invalid_attempts: Mapped[List["InvalidWordAttempt"]] = relationship(back_populates="game", cascade=CASCADE_RULES)


class GameTurn(Base):
    """Turn-by-turn data for Wordle UI recreation and analysis."""
    __tablename__ = 'game_turns'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey(GAME_ID_FK, ondelete='CASCADE'))
    turn_number: Mapped[int] = mapped_column(Integer)
    guess: Mapped[str] = mapped_column(String(5))
    reasoning: Mapped[Optional[str]] = mapped_column(Text)  # NULL for simple template
    is_correct: Mapped[bool] = mapped_column(Boolean)
    letter_results: Mapped[List[dict]] = mapped_column(JSONB)     # Full letter-by-letter feedback
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Relationships
    game: Mapped["Game"] = relationship(back_populates="turns")


class LLMInteraction(Base):
    """LLM interaction debugging and performance analysis."""
    __tablename__ = 'llm_interactions'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey(GAME_ID_FK, ondelete='CASCADE'))
    turn_number: Mapped[int] = mapped_column(Integer)
    prompt_text: Mapped[str] = mapped_column(Text)
    raw_response: Mapped[str] = mapped_column(Text)
    parse_success: Mapped[bool] = mapped_column(Boolean)
    parse_error_message: Mapped[Optional[str]] = mapped_column(Text)  # If parse failed
    extraction_method: Mapped[Optional[str]] = mapped_column(String(50))  # "quoted", "capitalized", etc.
    retry_attempt: Mapped[int] = mapped_column(Integer)  # Which retry (1st, 2nd, etc.)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)  # LLM response time
    
    # Usage tracking fields
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    reasoning_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    cost_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Relationships
    game: Mapped["Game"] = relationship(back_populates="llm_interactions")


class InvalidWordAttempt(Base):
    """Invalid word attempts for retry analysis."""
    __tablename__ = 'invalid_word_attempts'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey(GAME_ID_FK, ondelete='CASCADE'))
    turn_number: Mapped[int] = mapped_column(Integer)
    attempted_word: Mapped[str] = mapped_column(String(5))
    retry_attempt: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Relationships
    game: Mapped["Game"] = relationship(back_populates="invalid_attempts")


class GameUsageSummary(Base):
    """Database view for aggregated usage statistics per game."""
    __tablename__ = 'game_usage_summary'
    __table_args__ = {'info': {'is_view': True}}
    
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    total_tokens_input: Mapped[Optional[int]] = mapped_column(Integer)
    total_tokens_output: Mapped[Optional[int]] = mapped_column(Integer)
    total_tokens_reasoning: Mapped[Optional[int]] = mapped_column(Integer)
    total_tokens_all: Mapped[Optional[int]] = mapped_column(Integer)
    total_cost_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    response_time_avg_ms: Mapped[Optional[float]] = mapped_column(Float)
    total_requests: Mapped[int] = mapped_column(Integer)


# Production optimized indexes
Index('idx_games_daily_active', Game.model_name, Game.date)
Index('idx_games_date_status', Game.date, Game.status, Game.won)
Index('idx_games_model_performance', Game.model_name, Game.won, Game.guesses_count)
Index('idx_game_turns_game_id', GameTurn.game_id, GameTurn.turn_number)
Index('idx_llm_interactions_game_id', LLMInteraction.game_id, LLMInteraction.turn_number)
Index('idx_invalid_attempts_game_id', InvalidWordAttempt.game_id)
Index('idx_games_target_word', Game.target_word, Game.won)