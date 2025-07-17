"""Database service for Wordle benchmark game result persistence."""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, UTC
from uuid import UUID
import logging

from sqlalchemy import create_engine, Engine, select
from sqlalchemy.orm import sessionmaker, Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from wordle.models import GameResult
from database.models import Base, Game, GameTurn, LLMInteraction, InvalidWordAttempt
from database.config import DatabaseConfig

logger = logging.getLogger(__name__)


class GameDatabaseService:
    """Service for persisting and querying Wordle game results."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize database service with configuration.
        
        Args:
            config: Database configuration instance
        """
        self.config = config
        self.engine: Engine = create_engine(
            config.database_url,
            echo=config.echo_sql
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine) # NOSONAR
    
    def create_tables(self) -> None:
        """Create all database tables. Use for testing or initial setup."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self) -> None:
        """Drop all database tables. Use for testing cleanup."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def save_game_result(self, game_result: GameResult, 
                        llm_interactions: Optional[List[Dict[str, Any]]] = None) -> UUID:
        """Save a complete game result to the database.
        
        Args:
            game_result: Pydantic GameResult model
            llm_interactions: Optional list of LLM interaction data
            
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
                GameDatabaseService._add_invalid_word_attempts(session, game.id, game_result)
                
                session.commit()
                logger.info(f"Game result saved successfully with ID: {game.id}")
                return game.id
                
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to save game result: {e}")
                raise
    
    def get_game_by_id(self, game_id: UUID) -> Optional[Game]:
        """Retrieve a game by its ID with all relationships loaded.
        
        Args:
            game_id: UUID of the game
            
        Returns:
            Game model or None if not found
        """
        with self.SessionLocal() as session:
            try:
                stmt = select(Game).options(
                    selectinload(Game.turns),
                    selectinload(Game.invalid_attempts),
                    selectinload(Game.llm_interactions)
                ).where(Game.id == game_id)
                result = session.execute(stmt)
                game = result.scalar_one_or_none()
                if game:
                    session.expunge(game)  # Detach so it works outside session
                return game
            except SQLAlchemyError as e:
                logger.error(f"Failed to retrieve game {game_id}: {e}")
                raise
    
    def get_games_by_date(self, target_date: date) -> List[Game]:
        """Retrieve all games for a specific date.
        
        Args:
            target_date: Date to query
            
        Returns:
            List of Game models
        """
        with self.SessionLocal() as session:
            try:
                stmt = select(Game).where(Game.date == target_date)
                result = session.execute(stmt)
                return list(result.scalars().all())
            except SQLAlchemyError as e:
                logger.error(f"Failed to retrieve games for date {target_date}: {e}")
                raise
    
    def get_games_by_model(self, model_name: str, limit: Optional[int] = None) -> List[Game]:
        """Retrieve games by model name.
        
        Args:
            model_name: Name of the LLM model
            limit: Optional limit on number of results
            
        Returns:
            List of Game models
        """
        with self.SessionLocal() as session:
            try:
                stmt = select(Game).where(Game.model_name == model_name)
                if limit:
                    stmt = stmt.limit(limit)
                result = session.execute(stmt)
                return list(result.scalars().all())
            except SQLAlchemyError as e:
                logger.error(f"Failed to retrieve games for model {model_name}: {e}")
                raise

    @staticmethod
    def _convert_to_game_model(game_result: GameResult) -> Game:
        """Convert Pydantic GameResult to SQLAlchemy Game model."""
        game_state = game_result.game_state
        metadata = game_result.metadata
        
        # Parse date string to date object
        game_date = datetime.strptime(metadata.date, "%Y-%m-%d").date()
        
        return Game(
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
            created_at=datetime.now(UTC),
            completed_at=metadata.end_time
        )

    @staticmethod
    def _add_game_turns(session: Session, game_id: UUID, game_result: GameResult) -> None:
        """Add game turns to the database."""
        game_state = game_result.game_state
        
        for turn_number, guess in enumerate(game_state.guesses, 1):
            # Get reasoning if available
            reasoning = None
            if (turn_number - 1) < len(game_state.guess_reasoning):
                reasoning = game_state.guess_reasoning[turn_number - 1]
            
            # Get letter results
            letter_results = []
            if (turn_number - 1) < len(game_state.guess_results):
                letter_results = [
                    {
                        "position": lr.position,
                        "letter": lr.letter,
                        "status": lr.status.value
                    }
                    for lr in game_state.guess_results[turn_number - 1]
                ]
            
            # Check if this guess was correct
            is_correct = guess.lower() == game_state.target_word.lower()
            
            turn = GameTurn(
                game_id=game_id,
                turn_number=turn_number,
                guess=guess,
                reasoning=reasoning,
                is_correct=is_correct,
                letter_results=letter_results
            )
            session.add(turn)
    
    @staticmethod
    def _add_llm_interactions(session: Session, game_id: UUID,
                            llm_interactions: List[Dict[str, Any]]) -> None:
        """Add LLM interactions to the database."""
        for interaction_data in llm_interactions:
            interaction = LLMInteraction(
                game_id=game_id,
                turn_number=interaction_data.get('turn_number'),
                prompt_text=interaction_data.get('prompt_text', ''),
                raw_response=interaction_data.get('raw_response', ''),
                parse_success=interaction_data.get('parse_success', True),
                parse_error_message=interaction_data.get('parse_error_message'),
                extraction_method=interaction_data.get('extraction_method'),
                attempt_number=interaction_data.get('attempt_number', 1),
                response_time_ms=interaction_data.get('response_time_ms'),
                prompt_tokens=interaction_data.get('prompt_tokens'),
                completion_tokens=interaction_data.get('completion_tokens'),
                reasoning_tokens=interaction_data.get('reasoning_tokens'),
                total_tokens=interaction_data.get('total_tokens'),
                cost_usd=interaction_data.get('cost_usd')
            )
            session.add(interaction)
    
    @staticmethod
    def _add_invalid_word_attempts(session: Session, game_id: UUID,
                                 game_result: GameResult) -> None:
        """Add invalid word attempts to the database."""
        invalid_attempts = game_result.metadata.invalid_word_attempts
        
        for attempt_number, invalid_word in enumerate(invalid_attempts, 1):
            # Note: We don't have turn_number info for invalid attempts in the current model
            # This would need to be enhanced in the GameResult model to track which turn
            # For now, we'll set turn_number to 0 to indicate it's not tied to a specific turn
            attempt = InvalidWordAttempt(
                game_id=game_id,
                turn_number=0,  # Would need enhancement to track the actual turn
                attempted_word=invalid_word,
                attempt_number=attempt_number
            )
            session.add(attempt)