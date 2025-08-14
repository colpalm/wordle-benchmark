"""Database service for Wordle benchmark game result persistence."""

import logging
from datetime import UTC, date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import Engine, bindparam, create_engine, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, noload, selectinload, sessionmaker
from sqlalchemy.sql import Select

from database.config import DatabaseConfig
from database.models import (
    Game as GameModel,
)
from database.models import (
    GameTurn as GameTurnModel,
)
from database.models import (
    InvalidWordAttempt,
    LeaderboardStats,
    LLMInteraction,
)
from wordle.dtos import (
    GameDto,
    LeaderboardEntryDto,
    LeaderboardMetadataDto,
    LeaderboardResponseDto,
    LeaderboardStatsDto,
    RecentGameDto,
)
from wordle.models import GameResult

logger = logging.getLogger(__name__)


class GameDatabaseService:
    """Service for persisting and querying Wordle game results."""

    def __init__(self, config: DatabaseConfig):
        """Initialize database service with configuration.

        Args:
            config: Database configuration instance
        """
        self.config = config
        self.engine: Engine = create_engine(config.database_url, echo=config.echo_sql)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)  # NOSONAR

    def save_game_result(
        self,
        game_result: GameResult,
        llm_interactions: Optional[List[Dict[str, Any]]] = None,
        invalid_word_attempts: Optional[List[Dict[str, Any]]] = None,
    ) -> UUID:
        """Save a complete game result to the database.

        Args:
            game_result: Pydantic GameResult model
            llm_interactions: Optional list of LLM interaction data
            invalid_word_attempts: Optional list of dicts with word and turn info for invalid words

        Returns:
            UUID of the saved game

        Raises:
            SQLAlchemyError: If database operation fails
        """
        with self.SessionLocal() as session:
            try:
                # Convert GameResult to Game model
                game = GameDatabaseService._convert_to_game_model(game_result)
                session.add(game)
                session.flush()  # Get the generated game ID

                # Add game turns
                GameDatabaseService._add_game_turns(session, game.id, game_result)

                # Add LLM interactions if provided
                if llm_interactions:
                    GameDatabaseService._add_llm_interactions(session, game.id, llm_interactions)

                # Add invalid word attempts
                if invalid_word_attempts:
                    GameDatabaseService._add_invalid_word_attempts(session, game.id, invalid_word_attempts)

                session.commit()
                logger.info(f"Game result saved successfully with ID: {game.id}")
                return game.id

            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to save game result: {e}")
                raise

    def get_game_by_id(self, game_id: UUID, include_relationships: bool = False) -> Optional[GameDto]:
        """Retrieve a game by its ID with optional relationships loaded.

        Args:
            game_id: UUID of the game
            include_relationships: Whether to load turns, llm_interactions, and invalid_attempts

        Returns:
            GameDto or None if not found
        """
        with self.SessionLocal() as session:
            try:
                stmt = self._game_select(include_relationships).where(GameModel.id == game_id)
                result = session.execute(stmt)
                sqlalchemy_game = result.scalar_one_or_none()

                if sqlalchemy_game:
                    return GameDto.model_validate(sqlalchemy_game, from_attributes=True)
                return None
            except SQLAlchemyError as e:
                logger.error(f"Failed to retrieve game {game_id}: {e}")
                raise

    def get_games_by_date(self, target_date: date, include_relationships: bool = False) -> List[GameDto]:
        """Retrieve all games for a specific date.

        Args:
            target_date: Date to query
            include_relationships: Whether to load turns, llm_interactions, and invalid_attempts

        Returns:
            List of GameDto instances with optional relationships loaded
        """
        with self.SessionLocal() as session:
            try:
                stmt = self._game_select(include_relationships).where(GameModel.date == target_date)
                result = session.execute(stmt)
                sqlalchemy_games = list(result.scalars().all())

                # Convert SQLAlchemy models to DTOs using Pydantic's from_attributes
                game_dtos = [GameDto.model_validate(game, from_attributes=True) for game in sqlalchemy_games]

                logger.info(f"Retrieved {len(game_dtos)} games for date {target_date}")
                return game_dtos

            except SQLAlchemyError as e:
                logger.error(f"Failed to retrieve games for date {target_date}: {e}")
                raise

    @staticmethod
    def _game_select(relationships: bool) -> Select:
        """
        Base SELECT for GameModel with optional relationship loading.
        """

        stmt = select(GameModel)
        if relationships:
            return stmt.options(
                selectinload(GameModel.turns),
                selectinload(GameModel.invalid_attempts),
                selectinload(GameModel.llm_interactions),
            )
        else:
            return stmt.options(
                noload(GameModel.turns),
                noload(GameModel.invalid_attempts),
                noload(GameModel.llm_interactions),
            )


    def get_games_by_model(self, model_name: str, limit: Optional[int] = None) -> List[GameDto]:
        """Retrieve games by model name.

        Args:
            model_name: Name of the LLM model
            limit: Optional limit on number of results

        Returns:
            List of GameDto instances
        """
        with self.SessionLocal() as session:
            try:
                stmt = select(GameModel).where(GameModel.model_name == model_name)
                if limit:
                    stmt = stmt.limit(limit)
                result = session.execute(stmt)
                sqlalchemy_games = list(result.scalars().all())

                # Convert SQLAlchemy models to DTOs using Pydantic's from_attributes
                game_dtos = [GameDto.model_validate(game, from_attributes=True) for game in sqlalchemy_games]

                logger.info(f"Retrieved {len(game_dtos)} games for model {model_name}")
                return game_dtos

            except SQLAlchemyError as e:
                logger.error(f"Failed to retrieve games for model {model_name}: {e}")
                raise

    @staticmethod
    def _convert_to_game_model(game_result: GameResult) -> GameModel:
        """Convert Pydantic GameResult to SQLAlchemy Game model."""
        game_state = game_result.game_state
        metadata = game_result.metadata

        # Parse date string to date object
        game_date = datetime.strptime(metadata.date, "%Y-%m-%d").date()

        return GameModel(
            model_name=metadata.model,
            template_name=metadata.template,
            parser_name=metadata.parser,
            target_word=game_state.target_word,
            date=game_date,
            status=game_state.status.value,
            guesses_count=game_state.guesses_made,
            won=game_state.won,
            duration_seconds=metadata.duration_seconds,
            total_invalid_attempts=metadata.total_invalid_attempts,
            golf_score=game_result.golf_score,
            created_at=datetime.now(UTC),
            completed_at=metadata.end_time,
        )

    @staticmethod
    def _add_game_turns(session: Session, game_id: UUID, game_result: GameResult) -> None:
        """Add game turns to the database."""
        game_state = game_result.game_state

        for turn_index, guess in enumerate(game_state.guesses):
            # Get reasoning if available
            reasoning = None
            if turn_index < len(game_state.guess_reasoning):
                reasoning = game_state.guess_reasoning[turn_index]

            # Get letter results
            letter_results = []
            if turn_index < len(game_state.guess_results):
                letter_results = [
                    {"position": lr.position, "letter": lr.letter, "status": lr.status.value}
                    for lr in game_state.guess_results[turn_index]
                ]

            # Check if this guess was correct
            is_correct = guess.lower() == game_state.target_word.lower()

            turn = GameTurnModel(
                game_id=game_id,
                turn_number=turn_index + 1, # Convert to 1-based for database
                guess=guess,
                reasoning=reasoning,
                is_correct=is_correct,
                letter_results=letter_results,
            )
            session.add(turn)

    @staticmethod
    def _add_llm_interactions(session: Session, game_id: UUID, llm_interactions: List[Dict[str, Any]]) -> None:
        """Add LLM interactions to the database."""
        for interaction_data in llm_interactions:
            interaction = LLMInteraction(
                game_id=game_id,
                turn_number=interaction_data.get("turn_number"),
                prompt_text=interaction_data.get("prompt_text", ""),
                raw_response=interaction_data.get("raw_response", ""),
                parse_success=interaction_data.get("parse_success", True),
                parse_error_message=interaction_data.get("parse_error_message"),
                attempt_number=interaction_data.get("attempt_number", 1),
                response_time_ms=interaction_data.get("response_time_ms"),
                prompt_tokens=interaction_data.get("prompt_tokens"),
                completion_tokens=interaction_data.get("completion_tokens"),
                reasoning_tokens=interaction_data.get("reasoning_tokens"),
                total_tokens=interaction_data.get("total_tokens"),
                cost_usd=interaction_data.get("cost_usd"),
            )
            session.add(interaction)

    @staticmethod
    def _add_invalid_word_attempts(
        session: Session, game_id: UUID, invalid_word_attempts: List[Dict[str, Any]]
    ) -> None:
        """Add invalid word attempts to the database."""
        for invalid_attempt in invalid_word_attempts:
            # Create InvalidWordAttempt object with proper game_id and turn number
            attempt = InvalidWordAttempt(
                game_id=game_id,
                turn_number=invalid_attempt["turn_number"],
                attempted_word=invalid_attempt["word"],
                attempt_number=invalid_attempt["attempt_number"],
            )
            session.add(attempt)


class LeaderboardService:
    """Service for querying leaderboard statistics and recent game data."""

    def __init__(self, db_service: GameDatabaseService):
        """Initialize leaderboard service with database service.

        Args:
            db_service: GameDatabaseService instance for database operations
        """
        self.db_service = db_service

    def get_leaderboard_stats(self) -> List[LeaderboardStatsDto]:
        """Get leaderboard statistics for all models from database view.

        Returns:
            List of LeaderboardStatsDto models ordered by win rate descending

        Raises:
            SQLAlchemyError: If database operation fails
        """
        with self.db_service.SessionLocal() as session:
            try:
                stmt = select(LeaderboardStats).order_by(LeaderboardStats.win_rate.desc())
                result = session.execute(stmt)
                sqlalchemy_stats = list(result.scalars().all())

                # Convert SQLAlchemy models to DTOs using Pydantic's from_attributes
                stats_dtos = [
                    LeaderboardStatsDto.model_validate(stat, from_attributes=True) for stat in sqlalchemy_stats
                ]

                logger.info(f"Retrieved leaderboard stats for {len(stats_dtos)} models")
                return stats_dtos

            except SQLAlchemyError as e:
                logger.error(f"Failed to retrieve leaderboard stats: {e}")
                raise

    def get_recent_games_by_model(self, limit: int = 5) -> Dict[str, List[RecentGameDto]]:
        """Get recent games for each model for recent form display.

        Args:
            limit: Number of recent games per model to retrieve

        Returns:
            Dictionary mapping model_name to list of RecentGameDto models

        Raises:
            SQLAlchemyError: If database operation fails
        """
        with self.db_service.SessionLocal() as session:
            try:
                # Windowed subquery: rank games per model by date, created_at
                ranked = select(
                    GameModel.model_name,
                    GameModel.won,
                    GameModel.date,
                    func.row_number()
                    .over(
                        partition_by=GameModel.model_name,
                        order_by=(GameModel.date.desc(), GameModel.created_at.desc()),
                    )
                    .label("game_rank"),
                ).subquery("recent_games")

                stmt = (
                    select(ranked.c.model_name, ranked.c.won, ranked.c.date)
                    .where(ranked.c.game_rank <= bindparam("limit"))
                    .order_by(ranked.c.model_name, ranked.c.date.desc())
                )

                rows = session.execute(stmt, {"limit": limit}).fetchall()

                # Group by model and create DTOs
                recent_games_by_model = {}
                for row in rows:
                    model_name = row.model_name
                    if model_name not in recent_games_by_model:
                        recent_games_by_model[model_name] = []

                    recent_game = RecentGameDto(game_date=row.date, won=row.won)
                    recent_games_by_model[model_name].append(recent_game)

                logger.info(f"Retrieved recent games for {len(recent_games_by_model)} models")
                return recent_games_by_model

            except SQLAlchemyError as e:
                logger.error(f"Failed to retrieve recent games: {e}")
                raise

    def get_leaderboard_data(self, recent_games_limit: int = 5) -> LeaderboardResponseDto:
        """Get complete leaderboard data including stats and recent games.

        Args:
            recent_games_limit: Number of recent games per model for recent form

        Returns:
            LeaderboardResponseDto with complete leaderboard data

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Get leaderboard statistics
            leaderboard_stats = self.get_leaderboard_stats()

            # Get recent games for all models
            recent_games_by_model = self.get_recent_games_by_model(recent_games_limit)

            # Transform to DTOs
            leaderboard_entries = []
            for stats in leaderboard_stats:
                entry = LeaderboardEntryDto(
                    model_name=stats.model_name,
                    total_games=stats.total_games,
                    wins=stats.wins,
                    win_rate=round(float(stats.win_rate), 1),
                    avg_guesses=round(float(stats.avg_guesses), 1) if stats.avg_guesses else None,
                    total_golf_score=stats.total_golf_score,
                    first_game_date=stats.first_game_date,
                    last_game_date=stats.last_game_date,
                    recent_form=recent_games_by_model.get(stats.model_name, []),
                )
                leaderboard_entries.append(entry)

            # Calculate metadata
            total_games = sum(stat.total_games for stat in leaderboard_stats)
            metadata = LeaderboardMetadataDto(
                total_games=total_games, total_models=len(leaderboard_stats), last_updated=datetime.now(UTC)
            )

            return LeaderboardResponseDto(leaderboard=leaderboard_entries, metadata=metadata)

        except Exception as e:
            logger.error(f"Failed to get complete leaderboard data: {e}")
            raise
