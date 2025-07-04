import pytest
from datetime import datetime
from unittest.mock import patch

from llm_integration.openrouter_client import OpenRouterClient
from utils.logging_config import get_logger
from wordle.game_runner import GameRunner
from wordle.prompt_templates import PromptTemplateFactory
from wordle.response_parser import ResponseParserFactory
from llm_integration.llm_client import LLMError

logger = get_logger(__name__)


# Helper fixtures and mocks
@pytest.fixture
def llm_client():
    """Create a LLM client for testing."""
    return OpenRouterClient(api_key="test-key", model="test-model")

@pytest.fixture
def template():
    """Create a template for testing."""
    return PromptTemplateFactory.create_template("json") # using json since that is the current default

@pytest.fixture
def parser():
    """Create a parser for testing."""
    return ResponseParserFactory.create_parser("json")


@pytest.fixture
def game_runner(word_list, llm_client, template, parser):
    """Create a GameRunner instance with mocked dependencies."""
    return GameRunner(
        word_list=word_list,
        llm_client=llm_client,
        prompt_template=template,
        response_parser=parser,
        target_word="CRANE"
    )


class TestGameRunner:
    """Unit tests for individual GameRunner methods."""

    def test_initialize_game_with_target_word(self, game_runner, word_list):
        """
        Test game initialization with a custom target word.
        Given a GameRunner with a target word
        When we initialize the game,
        Then the game should be initialized with the target word
        """
        assert game_runner.game is None

        game_runner._initialize_game()

        assert game_runner.game is not None
        assert game_runner.game.target_word == "CRANE"
        assert game_runner.game.word_list == word_list

    def test_make_guess_attempt_success(self, game_runner, llm_client):
        """
        Given a GameRunner with a target word
        When I make a guess attempt
        Then the game should be updated with the guess and reasoning
        """
        game_runner._initialize_game()

        # Mock just the method we need
        json_response = '{"reasoning": "Starting with common letters", "guess": "STARE"}'
        with patch.object(llm_client, 'generate_response', return_value=json_response):
            game_runner._make_guess_attempt()

        assert game_runner.game.guesses[-1] == "STARE"
        assert game_runner.game.guess_reasoning[-1] == "Starting with common letters"

    def test_complete_winning_game(self, game_runner, llm_client):
        """
        Given I play a full game
        When I mock the json response with a winning response
        Then the game should be completed with a winning result
        """
        json_responses = [
            '{"reasoning": "Starting with vowels and common consonants", "guess": "STARE"}',
            '{"reasoning": "Based on feedback, trying the target word", "guess": "CRANE"}'
        ]

        with patch.object(llm_client, 'generate_response', side_effect=json_responses):
            result = game_runner.run_complete_game()

        assert result["game_state"]["won"] is True
        assert result["game_state"]["guesses"] == ["STARE", "CRANE"]
        assert len(result["game_state"]["guess_reasoning"]) == 2

    def test_complete_losing_game(self, game_runner, llm_client):
        """
        Given I play a full game with 6 incorrect guesses
        When I mock the json responses with words that don't match the target
        Then the game should be completed with a losing result
        """
        # Target word is "CRANE" (from fixture), so these guesses will all be wrong
        json_responses = [
            '{"reasoning": "Starting with vowels and common consonants", "guess": "STARE"}',
            '{"reasoning": "Trying different vowel placement", "guess": "LIGHT"}',
            '{"reasoning": "Testing new consonant combinations", "guess": "MOUND"}',
            '{"reasoning": "Exploring different letter patterns", "guess": "FIFTY"}',
            '{"reasoning": "Trying another combination", "guess": "BUMPS"}',
            '{"reasoning": "Final attempt with remaining letters", "guess": "GHOST"}'
        ]

        with patch.object(llm_client, 'generate_response', side_effect=json_responses):
            result = game_runner.run_complete_game()

        assert result["game_state"]["won"] is False
        assert result["game_state"]["game_over"] is True
        assert result["game_state"]["status"] == "lost"
        assert result["game_state"]["guesses_made"] == 6
        assert result["game_state"]["guesses_remaining"] == 0
        assert result["game_state"]["target_word"] == "CRANE"
        assert result["game_state"]["guesses"] == ["STARE", "LIGHT", "MOUND", "FIFTY", "BUMPS", "GHOST"]
        assert len(result["game_state"]["guess_reasoning"]) == 6
        assert result["success"] is True

    def test_make_guess_attempt_llm_failure(self, game_runner, llm_client):
        """Test LLM failure handling during guess attempt."""
        # Given an initialized game
        game_runner._initialize_game()
        initial_guesses = len(game_runner.game.guesses)

        # When we make a guess attempt and get an LLMError
        with patch.object(llm_client, 'generate_response', side_effect=LLMError("Simulated LLM failure")):
            # Then it should raise the LLM error
            with pytest.raises(LLMError, match="Simulated LLM failure"):
                game_runner._make_guess_attempt()

        # And the game should not be updated
        assert len(game_runner.game.guesses) == initial_guesses

    def test_create_result_success(self, game_runner, llm_client):
        """Test successful result creation with real game data."""
        # Given a completed game
        game_runner._initialize_game()
        game_runner.start_time = datetime(2025, 1, 15, 10, 0, 0)

        # Simulate a won game by making an actual guess
        json_response = '{"reasoning": "This will win", "guess": "CRANE"}'
        with patch.object(llm_client, 'generate_response', return_value=json_response):
            game_runner._make_guess_attempt()

        # When we create the result
        with patch('wordle.game_runner.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 0, 30)
            mock_datetime.strftime = datetime.strftime

            with patch.object(game_runner, '_log_game_summary'):  # Skip logging for test
                result = game_runner._create_result()

        # Then the result should contain real game data
        assert result["success"] is True
        assert result["game_state"]["won"] is True
        assert result["game_state"]["target_word"] == "CRANE"
        assert result["game_state"]["guesses"] == ["CRANE"]
        assert result["metadata"]["model"] == "test-model"
        assert result["metadata"]["template"] == "json"
        assert result["metadata"]["parser"] == "json"
        assert result["metadata"]["duration_seconds"] == pytest.approx(30.0)

    def test_create_result_not_initialized(self, game_runner):
        """Test result creation when the game is not properly initialized."""
        # Given an uninitialized game runner (don't call _initialize_game())
        # game_runner fixture already has all components set up,
        # But we deliberately don't initialize the game

        # When we try to create the result
        result = game_runner._create_result()

        # Then it should return an error result
        assert result["success"] is False
        assert result["error"] == "Game not properly initialized"

    def test_create_error_result(self, game_runner):
        """Test error result creation."""
        # Given a runner with start time
        game_runner.start_time = datetime(2025, 1, 15, 10, 0, 0)

        # When we create an error result
        with patch('wordle.game_runner.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 0, 15)

            result = game_runner._create_error_result("Something went wrong")

        # Then the error result should be properly formatted
        assert result["success"] is False
        assert result["error"] == "Something went wrong"
        assert result["metadata"]["model"] == "test-model"
        assert result["metadata"]["template"] == "json"
        assert result["metadata"]["parser"] == "json"
        assert result["metadata"]["duration_seconds"] == pytest.approx(15.0)
