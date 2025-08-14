"""Integration tests for database service using testcontainers."""

import os
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import text

from database.models import Base
from database.schema import (
    DROP_GAME_USAGE_SUMMARY_VIEW,
    DROP_LEADERBOARD_STATS_VIEW,
    GAME_USAGE_SUMMARY_VIEW,
    LEADERBOARD_STATS_VIEW,
)
from database.service import GameDatabaseService, LeaderboardService
from wordle.enums import GameStatus, LetterStatus
from wordle.models import GameMetadata, GameResult, GameState, LetterResult


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
    os.environ["TEST_DATABASE_URL"] = test_url

    # Create service
    service = GameDatabaseService(db_config)

    # Create tables using SQLAlchemy metadata directly (exclude views)
    tables_to_create = [table for table in Base.metadata.tables.values() if not table.info.get("is_view", False)]
    Base.metadata.create_all(bind=service.engine, tables=tables_to_create)

    # Create views for database functionality
    with service.engine.connect() as conn:
        conn.execute(text(GAME_USAGE_SUMMARY_VIEW))
        conn.execute(text(LEADERBOARD_STATS_VIEW))
        conn.commit()

    yield service

    # Cleanup views and tables
    with service.engine.connect() as conn:
        conn.execute(text(DROP_LEADERBOARD_STATS_VIEW))
        conn.execute(text(DROP_GAME_USAGE_SUMMARY_VIEW))
        conn.commit()

    # Drop tables using SQLAlchemy metadata directly (exclude views)
    tables_to_drop = [table for table in Base.metadata.tables.values() if not table.info.get("is_view", False)]
    Base.metadata.drop_all(bind=service.engine, tables=tables_to_drop)

    if "TEST_DATABASE_URL" in os.environ:
        del os.environ["TEST_DATABASE_URL"]


@pytest.mark.integration
class TestGameDatabaseService:
    """Integration tests for GameDatabaseService."""

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
                    LetterResult(position=4, letter="E", status=LetterStatus.PRESENT),
                ],
                [  # TESTS vs TESTS
                    LetterResult(position=0, letter="T", status=LetterStatus.CORRECT),
                    LetterResult(position=1, letter="E", status=LetterStatus.CORRECT),
                    LetterResult(position=2, letter="S", status=LetterStatus.CORRECT),
                    LetterResult(position=3, letter="T", status=LetterStatus.CORRECT),
                    LetterResult(position=4, letter="S", status=LetterStatus.CORRECT),
                ],
            ],
            guesses_made=2,
            guesses_remaining=4,
            status=GameStatus.WON,
            won=True,
            game_over=True,
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
            total_invalid_attempts=0,
        )

        golf_score = game_state.guesses_made - 4

        game_result = GameResult(
            success=True, game_state=game_state, metadata=metadata, error=None, golf_score=golf_score
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
                    LetterResult(position=4, letter="D", status=LetterStatus.ABSENT),
                ]
            ],
            guesses_made=1,
            guesses_remaining=5,
            status=GameStatus.IN_PROGRESS,
            won=False,
            game_over=False,
        )

        metadata = GameMetadata(
            model="test-model",
            template="simple",
            parser="simple",
            duration_seconds=30.0,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC),
            date="2024-01-15",
            total_invalid_attempts=2,
        )

        golf_score = game_state.guesses_made - 4

        game_result = GameResult(success=True, game_state=game_state, metadata=metadata, golf_score=golf_score)

        # Prepare invalid word attempts in consolidated structure
        invalid_word_attempts = [
            {"word": "XYZZZ", "turn_number": 1, "attempt_number": 1},
            {"word": "QWRTY", "turn_number": 1, "attempt_number": 2},
        ]

        # Save with invalid attempts
        game_id = db_service.save_game_result(game_result, None, invalid_word_attempts)

        # Verify
        saved_game = db_service.get_game_by_id(game_id, include_relationships=True)
        assert saved_game.total_invalid_attempts == 2

        # Verify invalid attempts were saved (and invalid attempts are present when include_relationships=True)
        assert saved_game.total_invalid_attempts == 2
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
                guess_results=[
                    [LetterResult(position=j, letter=f"WORD{i}"[j], status=LetterStatus.ABSENT) for j in range(5)]
                ],
                guesses_made=1,
                guesses_remaining=5,
                status=GameStatus.IN_PROGRESS,
                won=False,
                game_over=False,
            )

            metadata = GameMetadata(
                model=f"model-{i}",
                template="simple",
                parser="simple",
                duration_seconds=30.0,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                date="2024-01-15",
            )

            golf_score = game_state.guesses_made - 4

            game_result = GameResult(success=True, game_state=game_state, metadata=metadata, golf_score=golf_score)

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
                guess_results=[
                    [LetterResult(position=j, letter=f"WORD{i}"[j], status=LetterStatus.ABSENT) for j in range(5)]
                ],
                guesses_made=1,
                guesses_remaining=5,
                status=GameStatus.IN_PROGRESS,
                won=False,
                game_over=False,
            )

            metadata = GameMetadata(
                model=model,
                template="simple",
                parser="simple",
                duration_seconds=30.0,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                date="2024-01-15",
            )

            golf_score = game_state.guesses_made - 4

            game_result = GameResult(success=True, game_state=game_state, metadata=metadata, golf_score=golf_score)

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
                    LetterResult(position=4, letter="D", status=LetterStatus.ABSENT),
                ]
            ],
            guesses_made=1,
            guesses_remaining=5,
            status=GameStatus.IN_PROGRESS,
            won=False,
            game_over=False,
        )

        metadata = GameMetadata(
            model="test-model",
            template="json",
            parser="json",
            duration_seconds=30.0,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC),
            date="2024-01-15",
        )

        golf_score = game_state.guesses_made - 4

        game_result = GameResult(success=True, game_state=game_state, metadata=metadata, golf_score=golf_score)

        # Create LLM interactions data
        llm_interactions = [
            {
                "turn_number": 1,
                "prompt_text": "What is your first guess?",
                "raw_response": "I think WORLD would be a good starting word.",
                "parse_success": True,
                "attempt_number": 1,
                "response_time_ms": 1500,
            }
        ]

        # Save with LLM interactions
        game_id = db_service.save_game_result(game_result, llm_interactions)

        # Verify LLM interactions are accessible
        saved_game = db_service.get_game_by_id(game_id, include_relationships=True)
        assert saved_game is not None

        # SQLAlchemy relationships are iterable at runtime despite type warnings
        assert len(saved_game.llm_interactions) == 1

        interaction = saved_game.llm_interactions[0]
        assert interaction.turn_number == 1
        assert interaction.prompt_text == "What is your first guess?"
        assert interaction.raw_response == "I think WORLD would be a good starting word."
        assert interaction.parse_success is True
        assert interaction.attempt_number == 1
        assert interaction.response_time_ms == 1500


@pytest.fixture
def leaderboard_service(db_service):
    """Leaderboard service fixture with test database."""
    return LeaderboardService(db_service)


def create_sample_game_result(
    model_name: str, won: bool, guesses_made: int, target_word: str, game_date: str = "2024-01-15"
) -> GameResult:
    """Helper function to create sample game results for testing."""
    # Create valid 5-letter guesses
    sample_guesses = ["CRANE", "STARE", "WORLD", "LIGHT", "MOUND", "GHOST"]
    guesses = sample_guesses[:guesses_made]

    game_state = GameState(
        target_word=target_word,
        guesses=guesses,
        guess_reasoning=[None] * guesses_made,
        guess_results=[
            [
                LetterResult(position=j, letter=chr(65 + j), status=LetterStatus.ABSENT) for j in range(5)
            ]  # A, B, C, D, E
            for _ in range(guesses_made)
        ],
        guesses_made=guesses_made,
        guesses_remaining=6 - guesses_made,
        status=GameStatus.WON if won else GameStatus.LOST,
        won=won,
        game_over=True,
    )

    metadata = GameMetadata(
        model=model_name,
        template="json",
        parser="json",
        duration_seconds=30.0,
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        date=game_date,
        total_invalid_attempts=0,
    )

    # Calculate golf score: won games = guesses - 4, lost games = +4
    golf_score = guesses_made - 4 if won else 4

    return GameResult(success=True, game_state=game_state, metadata=metadata, golf_score=golf_score)


@pytest.mark.integration
class TestLeaderboardService:
    """Integration tests for LeaderboardService."""

    def test_leaderboard_with_no_games(self, leaderboard_service):
        """Test leaderboard service when no games exist."""
        response = leaderboard_service.get_leaderboard_data()

        assert response.leaderboard == []
        assert response.metadata.total_games == 0
        assert response.metadata.total_models == 0
        assert response.metadata.last_updated is not None

    def test_leaderboard_with_single_model_multiple_games(self, db_service, leaderboard_service):
        """Test leaderboard with multiple games from a single model."""
        model_name = "test-model-1"

        # Create sample games: 3 wins, 2 losses
        games = [
            create_sample_game_result(model_name, won=True, guesses_made=3, target_word="TEST1"),  # Golf: -1
            create_sample_game_result(model_name, won=True, guesses_made=4, target_word="TEST2"),  # Golf: 0
            create_sample_game_result(model_name, won=True, guesses_made=5, target_word="TEST3"),  # Golf: +1
            create_sample_game_result(model_name, won=False, guesses_made=6, target_word="TEST4"),  # Golf: +4
            create_sample_game_result(model_name, won=False, guesses_made=6, target_word="TEST5"),  # Golf: +4
        ]

        # Save all games
        for game_result in games:
            db_service.save_game_result(game_result)

        # Get leaderboard data
        response = leaderboard_service.get_leaderboard_data()

        # Verify response structure
        assert len(response.leaderboard) == 1
        assert response.metadata.total_games == len(games)
        assert response.metadata.total_models == 1

        # Verify model statistics
        model_stats = response.leaderboard[0]
        assert model_stats.model_name == model_name
        assert model_stats.total_games == len(games)
        assert model_stats.wins == 3
        assert model_stats.win_rate == pytest.approx(60.0)  # 3/5 * 100
        assert model_stats.avg_guesses == pytest.approx(4.0)  # (3+4+5)/3 = 4.0 (only won games)
        assert model_stats.total_golf_score == 8  # Expected: -1 + 0 + 1 + 4 + 4 = 8
        assert model_stats.first_game_date == date(2024, 1, 15)
        assert model_stats.last_game_date == date(2024, 1, 15)
        assert len(model_stats.recent_form) == len(games)  # All 5 games

    def test_leaderboard_with_multiple_models(self, db_service, leaderboard_service):
        """Test leaderboard with multiple models competing."""
        # Model 1: Great performance
        model1_games = [
            create_sample_game_result("gpt-4o-test", won=True, guesses_made=3, target_word="TEST1"),  # Golf: -1
            create_sample_game_result("gpt-4o-test", won=True, guesses_made=3, target_word="TEST2"),  # Golf: -1
            create_sample_game_result("gpt-4o-test", won=True, guesses_made=4, target_word="TEST3"),  # Golf: 0
        ]

        # Model 2: Average performance
        model2_games = [
            create_sample_game_result("claude-3-test", won=True, guesses_made=4, target_word="TEST4"),  # Golf: 0
            create_sample_game_result("claude-3-test", won=True, guesses_made=5, target_word="TEST5"),  # Golf: +1
            create_sample_game_result("claude-3-test", won=False, guesses_made=6, target_word="TEST6"),  # Golf: +4
        ]

        # Model 3: Poor performance
        model3_games = [
            create_sample_game_result("gemini-test", won=False, guesses_made=6, target_word="TEST7"),  # Golf: +4
            create_sample_game_result("gemini-test", won=False, guesses_made=6, target_word="TEST8"),  # Golf: +4
        ]

        # Save all games
        all_games = model1_games + model2_games + model3_games
        for game_result in all_games:
            db_service.save_game_result(game_result)

        # Get leaderboard data
        response = leaderboard_service.get_leaderboard_data()

        # Verify response structure
        assert len(response.leaderboard) == 3
        assert response.metadata.total_games == len(all_games)
        assert response.metadata.total_models == 3

        # Verify models are sorted by win rate (descending)
        assert response.leaderboard[0].model_name == "gpt-4o-test"  # Highest win rate, 3/3
        assert response.leaderboard[1].model_name == "claude-3-test"  # Middle win rate, 2/3
        assert response.leaderboard[2].model_name == "gemini-test"  # Lowest win rate, 0/2

        # Verify win rates
        models_by_win_rate = {entry.model_name: entry.win_rate for entry in response.leaderboard}
        assert models_by_win_rate["gpt-4o-test"] == pytest.approx(100.0)  # 3/3
        assert models_by_win_rate["claude-3-test"] == pytest.approx(66.7)  # 2/3 (rounded to 1 decimal)
        assert models_by_win_rate["gemini-test"] == pytest.approx(0.0)  # 0/2

        # Verify win rates are in descending order
        win_rates = [entry.win_rate for entry in response.leaderboard]
        assert win_rates == sorted(win_rates, reverse=True)

        # Verify golf scores
        models_by_golf = {entry.model_name: entry.total_golf_score for entry in response.leaderboard}
        assert models_by_golf["gpt-4o-test"] == -2  # Expected: -1 + -1 + 0 = -2
        assert models_by_golf["claude-3-test"] == 5  # Expected: 0 + 1 + 4 = 5
        assert models_by_golf["gemini-test"] == 8  # Expected: 4 + 4 = 8

    def test_recent_games_query(self, db_service, leaderboard_service):
        """Test recent games functionality with specific dates."""
        model_name = "test-model"

        # Create games across different dates (most recent first in creation)
        games = [
            create_sample_game_result(
                model_name, won=True, guesses_made=3, target_word="TEST1", game_date="2024-01-20"
            ),
            create_sample_game_result(
                model_name, won=False, guesses_made=6, target_word="TEST2", game_date="2024-01-19"
            ),
            create_sample_game_result(
                model_name, won=True, guesses_made=4, target_word="TEST3", game_date="2024-01-18"
            ),
            create_sample_game_result(
                model_name, won=True, guesses_made=5, target_word="TEST4", game_date="2024-01-17"
            ),
            create_sample_game_result(
                model_name, won=False, guesses_made=6, target_word="TEST5", game_date="2024-01-16"
            ),
            create_sample_game_result(
                model_name, won=True, guesses_made=3, target_word="TEST6", game_date="2024-01-15"
            ),  # Should not appear in recent 5
        ]

        # Save all games
        for game_result in games:
            db_service.save_game_result(game_result)

        # Test recent games query
        recent_games = leaderboard_service.get_recent_games_by_model(limit=5)

        assert model_name in recent_games
        model_recent = recent_games[model_name]
        assert len(model_recent) == 5

        # Verify games are in date descending order (most recent first)
        dates = [game.game_date for game in model_recent]
        assert dates == [date(2024, 1, 20), date(2024, 1, 19), date(2024, 1, 18), date(2024, 1, 17), date(2024, 1, 16)]

        # Verify won/lost status matches
        results = [game.won for game in model_recent]
        assert results == [True, False, True, True, False]

    def test_leaderboard_with_no_won_games(self, db_service, leaderboard_service):
        """Test leaderboard when model has no won games (avg_guesses should be None)."""
        model_name = "failing-model"

        # Create only lost games
        games = [
            create_sample_game_result(model_name, won=False, guesses_made=6, target_word="TEST1"),
            create_sample_game_result(model_name, won=False, guesses_made=6, target_word="TEST2"),
        ]

        # Save games
        for game_result in games:
            db_service.save_game_result(game_result)

        # Get leaderboard data
        response = leaderboard_service.get_leaderboard_data()

        # Verify model stats
        assert len(response.leaderboard) == 1
        model_stats = response.leaderboard[0]
        assert model_stats.model_name == model_name
        assert model_stats.total_games == 2
        assert model_stats.wins == 0
        assert model_stats.win_rate == pytest.approx(0.0)
        assert model_stats.avg_guesses is None  # No won games to average
        assert model_stats.total_golf_score == 8  # 4 + 4 = 8 (all losses)
