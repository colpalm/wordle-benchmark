"""Integration tests for database service using testcontainers."""

import pytest
import os
from datetime import datetime, date, UTC

from database.service import GameDatabaseService
from wordle.models import GameResult, GameState, GameMetadata, LetterResult, UsageStats
from wordle.enums import GameStatus, LetterStatus


@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQL container fixture using testcontainers."""
    try:
        from testcontainers.postgres import PostgresContainer
        
        with PostgresContainer("postgres:15") as postgres:
            # Wait for the container to be ready
            postgres.start()
            yield postgres
    except ImportError:
        pytest.skip("testcontainers not available")


@pytest.fixture
def db_service(postgres_container, db_config):
    """Database service fixture with test database."""
    # Set the test database URL for our config
    test_url = postgres_container.get_connection_url()
    os.environ['TEST_DATABASE_URL'] = test_url
    
    # Create service and tables
    service = GameDatabaseService(db_config)
    service.create_tables()
    
    yield service
    
    # Cleanup
    service.drop_tables()
    if 'TEST_DATABASE_URL' in os.environ:
        del os.environ['TEST_DATABASE_URL']


@pytest.mark.integration
class TestGameDatabaseService:
    """Integration tests for GameDatabaseService."""
    
    def test_create_and_drop_tables(self, db_service):
        """Test table creation and cleanup."""
        # Tables should already be created by fixture
        # Just verify the service exists
        assert db_service is not None
        
        # Drop and recreate to test the methods
        db_service.drop_tables()
        db_service.create_tables()
    
    def test_save_simple_game_result(self, db_service):
        """Test saving a basic game result."""
        # Create a simple game result
        game_state = GameState(
            target_word="TESTS",
            guesses=["CRANE", "TESTS"],
            guess_reasoning=[None, None],  # Simple template
            guess_results=[
                [  # CRANE vs TESTS
                    LetterResult(position=0, letter="C", status=LetterStatus.ABSENT),
                    LetterResult(position=1, letter="R", status=LetterStatus.ABSENT),
                    LetterResult(position=2, letter="A", status=LetterStatus.ABSENT),
                    LetterResult(position=3, letter="N", status=LetterStatus.ABSENT),
                    LetterResult(position=4, letter="E", status=LetterStatus.PRESENT)
                ],
                [  # TESTS vs TESTS
                    LetterResult(position=0, letter="T", status=LetterStatus.CORRECT),
                    LetterResult(position=1, letter="E", status=LetterStatus.CORRECT),
                    LetterResult(position=2, letter="S", status=LetterStatus.CORRECT),
                    LetterResult(position=3, letter="T", status=LetterStatus.CORRECT),
                    LetterResult(position=4, letter="S", status=LetterStatus.CORRECT)
                ]
            ],
            guesses_made=2,
            guesses_remaining=4,
            status=GameStatus.WON,
            won=True,
            game_over=True
        )
        
        start_time = datetime.now(UTC)
        end_time = datetime.now(UTC)
        
        metadata = GameMetadata(
            model="openai/gpt-4o-mini",
            template="simple",
            parser="simple",
            duration_seconds=45.2,
            start_time=start_time,
            end_time=end_time,
            date="2024-01-15",
            invalid_word_attempts=[],
            total_invalid_attempts=0,
            usage_stats=UsageStats(
                total_requests=2,
                total_tokens_input=100,
                total_tokens_output=50,
                total_cost_usd=0.01,
                response_time_avg_ms=1200.0
            )
        )
        
        game_result = GameResult(
            success=True,
            game_state=game_state,
            metadata=metadata,
            error=None
        )
        
        # Save the game result
        game_id = db_service.save_game_result(game_result)
        
        # Verify it was saved
        assert game_id is not None
        
        # Retrieve and verify
        saved_game = db_service.get_game_by_id(game_id)
        assert saved_game is not None
        assert saved_game.model_name == "openai/gpt-4o-mini"
        assert saved_game.target_word == "TESTS"
        assert saved_game.won is True
        assert saved_game.guesses_count == 2
        assert saved_game.status == "won"
        assert saved_game.game_metadata == {}
    
    def test_save_game_with_invalid_attempts(self, db_service):
        """Test saving a game with invalid word attempts."""
        game_state = GameState(
            target_word="HELLO",
            guesses=["WORLD"],
            guess_reasoning=[None],
            guess_results=[
                [
                    LetterResult(position=0, letter="W", status=LetterStatus.ABSENT),
                    LetterResult(position=1, letter="O", status=LetterStatus.PRESENT),
                    LetterResult(position=2, letter="R", status=LetterStatus.ABSENT),
                    LetterResult(position=3, letter="L", status=LetterStatus.CORRECT),
                    LetterResult(position=4, letter="D", status=LetterStatus.ABSENT)
                ]
            ],
            guesses_made=1,
            guesses_remaining=5,
            status=GameStatus.IN_PROGRESS,
            won=False,
            game_over=False
        )
        
        metadata = GameMetadata(
            model="test-model",
            template="simple", 
            parser="simple",
            duration_seconds=30.0,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC),
            date="2024-01-15",
            invalid_word_attempts=["XYZZZ", "QWRTY"],
            total_invalid_attempts=2
        )
        
        game_result = GameResult(
            success=True,
            game_state=game_state,
            metadata=metadata
        )
        
        # Save with invalid attempts
        game_id = db_service.save_game_result(game_result)
        
        # Verify
        saved_game = db_service.get_game_by_id(game_id)
        assert saved_game.total_invalid_attempts == 2
        
        # SQLAlchemy relationships are iterable at runtime despite type warnings
        assert len(saved_game.invalid_attempts) == 2
        assert saved_game.invalid_attempts[0].attempted_word == "XYZZZ"
        assert saved_game.invalid_attempts[1].attempted_word == "QWRTY"
    
    def test_get_games_by_date(self, db_service):
        """Test retrieving games by date."""
        target_date = date(2024, 1, 15)
        
        # Create two games for the same date
        for i in range(2):
            game_state = GameState(
                target_word=f"TEST{i}",
                guesses=[f"WORD{i}"],
                guess_reasoning=[None],
                guess_results=[[
                    LetterResult(position=j, letter=f"WORD{i}"[j], status=LetterStatus.ABSENT)
                    for j in range(5)
                ]],
                guesses_made=1,
                guesses_remaining=5,
                status=GameStatus.IN_PROGRESS,
                won=False,
                game_over=False
            )
            
            metadata = GameMetadata(
                model=f"model-{i}",
                template="simple",
                parser="simple", 
                duration_seconds=30.0,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                date="2024-01-15"
            )
            
            game_result = GameResult(
                success=True,
                game_state=game_state,
                metadata=metadata
            )
            
            db_service.save_game_result(game_result)
        
        # Retrieve games by date
        games = db_service.get_games_by_date(target_date)
        assert len(games) == 2
        assert all(game.date == target_date for game in games)
    
    def test_get_games_by_model(self, db_service):
        """Test retrieving games by model name."""
        model_name = "test-model"
        
        # Create games with different models
        for i, model in enumerate([model_name, "other-model", model_name]):
            game_state = GameState(
                target_word=f"TEST{i}",
                guesses=[f"WORD{i}"],
                guess_reasoning=[None],
                guess_results=[[
                    LetterResult(position=j, letter=f"WORD{i}"[j], status=LetterStatus.ABSENT)
                    for j in range(5)
                ]],
                guesses_made=1,
                guesses_remaining=5,
                status=GameStatus.IN_PROGRESS,
                won=False,
                game_over=False
            )
            
            metadata = GameMetadata(
                model=model,
                template="simple",
                parser="simple",
                duration_seconds=30.0,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                date="2024-01-15"
            )
            
            game_result = GameResult(
                success=True,
                game_state=game_state,
                metadata=metadata
            )
            
            db_service.save_game_result(game_result)
        
        # Retrieve games by model
        games = db_service.get_games_by_model(model_name)
        assert len(games) == 2
        assert all(game.model_name == model_name for game in games)
    
    def test_save_game_with_llm_interactions(self, db_service):
        """Test saving a game with LLM interactions and accessing them."""
        game_state = GameState(
            target_word="HELLO",
            guesses=["WORLD"],
            guess_reasoning=["Starting with common letters"],
            guess_results=[
                [
                    LetterResult(position=0, letter="W", status=LetterStatus.ABSENT),
                    LetterResult(position=1, letter="O", status=LetterStatus.PRESENT),
                    LetterResult(position=2, letter="R", status=LetterStatus.ABSENT),
                    LetterResult(position=3, letter="L", status=LetterStatus.CORRECT),
                    LetterResult(position=4, letter="D", status=LetterStatus.ABSENT)
                ]
            ],
            guesses_made=1,
            guesses_remaining=5,
            status=GameStatus.IN_PROGRESS,
            won=False,
            game_over=False
        )
        
        metadata = GameMetadata(
            model="test-model",
            template="json",
            parser="json",
            duration_seconds=30.0,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC),
            date="2024-01-15"
        )
        
        game_result = GameResult(
            success=True,
            game_state=game_state,
            metadata=metadata
        )
        
        # Create LLM interactions data
        llm_interactions = [
            {
                "turn_number": 1,
                "prompt_text": "What is your first guess?",
                "raw_response": "I think WORLD would be a good starting word.",
                "parse_success": True,
                "extraction_method": "quoted",
                "attempt_number": 1,
                "response_time_ms": 1500
            }
        ]
        
        # Save with LLM interactions
        game_id = db_service.save_game_result(game_result, llm_interactions)
        
        # Verify LLM interactions are accessible
        saved_game = db_service.get_game_by_id(game_id)
        assert saved_game is not None
        
        # SQLAlchemy relationships are iterable at runtime despite type warnings  
        assert len(saved_game.llm_interactions) == 1
        
        interaction = saved_game.llm_interactions[0]
        assert interaction.turn_number == 1
        assert interaction.prompt_text == "What is your first guess?"
        assert interaction.raw_response == "I think WORLD would be a good starting word."
        assert interaction.parse_success is True
        assert interaction.extraction_method == "quoted"
        assert interaction.attempt_number == 1
        assert interaction.response_time_ms == 1500