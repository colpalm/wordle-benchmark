from datetime import datetime
from unittest.mock import patch

import pytest

from llm_integration.llm_client import LLMError
from llm_integration.openrouter_client import OpenRouterClient
from utils.logging_config import get_logger
from wordle.game_runner import GameRunner
from wordle.prompt_templates import PromptTemplateFactory
from wordle.response_parser import ResponseParserFactory

logger = get_logger(__name__)


# Helper fixtures and mocks
@pytest.fixture
def llm_client():
    """Create a LLM client for testing."""
    return OpenRouterClient(api_key="test-key", model="test-model")


@pytest.fixture
def template():
    """Create a template for testing."""
    return PromptTemplateFactory.create_template("json")  # using json since that is the current default


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
        target_word="CRANE",
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
        with patch.object(llm_client, "generate_response", return_value=json_response):
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
            '{"reasoning": "Based on feedback, trying the target word", "guess": "CRANE"}',
        ]

        with patch.object(llm_client, "generate_response", side_effect=json_responses):
            result = game_runner.run_complete_game()

        assert result.game_state.won is True
        assert result.game_state.guesses == ["STARE", "CRANE"]
        assert len(result.game_state.guess_reasoning) == 2
        assert result.golf_score == result.game_state.guesses_made - 4  # Won in 2 guesses: 2 - 4 = -2

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
            '{"reasoning": "Final attempt with remaining letters", "guess": "GHOST"}',
        ]

        with patch.object(llm_client, "generate_response", side_effect=json_responses):
            result = game_runner.run_complete_game()

        assert result.game_state.won is False
        assert result.game_state.game_over is True
        assert result.game_state.status == "lost"
        assert result.game_state.guesses_made == 6
        assert result.game_state.guesses_remaining == 0
        assert result.game_state.target_word == "CRANE"
        assert result.game_state.guesses == ["STARE", "LIGHT", "MOUND", "FIFTY", "BUMPS", "GHOST"]
        assert result.golf_score == 4  # Lost game = +4 penalty
        assert len(result.game_state.guess_reasoning) == 6
        assert result.success is True

    def test_make_guess_attempt_llm_failure(self, game_runner, llm_client):
        """Test LLM failure handling during guess attempt."""
        # Given an initialized game
        game_runner._initialize_game()
        initial_guesses = len(game_runner.game.guesses)

        # When we make a guess attempt and get an LLMError
        with patch.object(llm_client, "generate_response", side_effect=LLMError("Simulated LLM failure")):
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
        with patch.object(llm_client, "generate_response", return_value=json_response):
            game_runner._make_guess_attempt()

        # When we create the result
        with patch("wordle.game_runner.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 0, 30)
            mock_datetime.strftime = datetime.strftime

            with patch.object(game_runner, "_log_game_summary"):  # Skip logging for test
                result = game_runner._create_result()

        # Then the result should contain real game data
        assert result.success is True
        assert result.game_state.won is True
        assert result.game_state.target_word == "CRANE"
        assert result.game_state.guesses == ["CRANE"]
        assert result.metadata.model == "test-model"
        assert result.metadata.template == "json"
        assert result.metadata.parser == "json"
        assert result.metadata.duration_seconds == pytest.approx(30.0)

    def test_create_result_not_initialized(self, game_runner):
        """Test result creation when the game is not properly initialized."""
        # Given an uninitialized game runner (don't call _initialize_game())
        # game_runner fixture already has all components set up,
        # But we deliberately don't initialize the game

        # When we try to create the result
        result = game_runner._create_result()

        # Then it should return an error result
        assert result.success is False
        assert result.error == "Game not properly initialized"

    def test_create_error_result(self, game_runner):
        """Test error result creation."""
        # Given a runner with start time
        game_runner.start_time = datetime(2025, 1, 15, 10, 0, 0)

        # When we create an error result
        with patch("wordle.game_runner.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 0, 15)

            result = game_runner._create_error_result("Something went wrong")

        # Then the error result should be properly formatted
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.metadata.model == "test-model"
        assert result.metadata.template == "json"
        assert result.golf_score == 4  # Error treated as lost game = +4
        assert result.metadata.parser == "json"
        assert result.metadata.duration_seconds == pytest.approx(15.0)

    def test_create_error_result_with_partial_game_state(self, game_runner, llm_client):
        """Test error result creation preserves partial game state when available."""
        # Given a game that has been initialized and has some progress
        game_runner._initialize_game()
        game_runner.start_time = datetime(2025, 1, 15, 10, 0, 0)

        # Make a successful guess first to establish partial state
        json_response = '{"reasoning": "Starting with common letters", "guess": "STARE"}'
        with patch.object(llm_client, "generate_response", return_value=json_response):
            game_runner._make_guess_attempt()

        # Verify we have some game progress
        assert len(game_runner.game.guesses) == 1
        assert game_runner.game.guesses[0] == "STARE"

        # When we create an error result
        with patch("wordle.game_runner.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 0, 15)

            result = game_runner._create_error_result("Simulated failure after partial progress")

        # Then the error result should preserve the partial game state
        assert result.success is False
        assert result.error == "Simulated failure after partial progress"
        assert result.game_state is not None  # Key difference from basic error case

        # Verify partial state was preserved
        assert result.game_state.target_word == "CRANE"  # From fixture
        assert result.game_state.guesses == ["STARE"]
        assert result.game_state.guess_reasoning == ["Starting with common letters"]
        assert result.game_state.guesses_made == 1
        assert result.game_state.guesses_remaining == 5
        assert result.game_state.won is False
        # Game should be marked as over and lost when an error occurs
        assert result.game_state.game_over is True
        assert result.game_state.status.value == "lost"

        # Metadata should still be correct
        assert result.metadata.model == "test-model"
        assert result.metadata.duration_seconds == pytest.approx(15.0)


class TestGameRunnerRetryLogic:
    """Test suite for the new retry logic for invalid words and parsing failures."""

    def test_invalid_word_retry_success(self, game_runner, llm_client):
        """
        GIVEN a GameRunner with an initialized game
        WHEN the LLM first guesses an invalid word, then a valid word
        THEN the invalid word should be retried and the valid word should be accepted
        """
        game_runner._initialize_game()
        game_runner._current_turn_number = 1

        # Mock LLM responses: first invalid, then valid
        json_responses = [
            '{"reasoning": "Trying a random word", "guess": "ZXXCV"}',  # Invalid word
            '{"reasoning": "Trying a real word", "guess": "STARE"}',  # Valid word
        ]

        with patch.object(llm_client, "generate_response", side_effect=json_responses):
            game_runner._make_guess_attempt()

        # Should have made the valid guess
        assert game_runner.game.guesses[-1] == "STARE"
        assert game_runner.game.guess_reasoning[-1] == "Trying a real word"
        assert len(game_runner.game.guesses) == 1

        # Should have tracked the invalid attempt
        assert len(game_runner.invalid_word_attempts) == 1
        invalid_attempt = game_runner.invalid_word_attempts[0]
        assert invalid_attempt["word"] == "ZXXCV"
        assert invalid_attempt["turn_number"] == 1
        assert invalid_attempt["attempt_number"] == 1

    def test_invalid_word_multiple_retries_success(self, game_runner, llm_client):
        """
        GIVEN a GameRunner with an initialized game
        WHEN the LLM guesses multiple invalid words, then a valid word
        THEN all invalid words should be tracked and the valid word accepted
        """
        game_runner._initialize_game()
        game_runner._current_turn_number = 1

        # Mock LLM responses: two invalid, then valid
        json_responses = [
            '{"reasoning": "First try", "guess": "ZXXCV"}',  # Invalid
            '{"reasoning": "Second try", "guess": "QWERT"}',  # Invalid
            '{"reasoning": "Third try", "guess": "STARE"}',  # Valid
        ]

        with patch.object(llm_client, "generate_response", side_effect=json_responses):
            game_runner._make_guess_attempt()

        # Should have made the valid guess
        assert game_runner.game.guesses[-1] == "STARE"
        assert len(game_runner.game.guesses) == 1

        # Should have tracked both invalid attempts
        assert len(game_runner.invalid_word_attempts) == 2
        invalid_words = [attempt["word"] for attempt in game_runner.invalid_word_attempts]
        assert "ZXXCV" in invalid_words
        assert "QWERT" in invalid_words

    def test_invalid_across_multiple_guesses(self, game_runner, llm_client):
        """
        GIVEN a GameRunner with an initialized game
        WHEN the LLM guesses multiple times with invali and valid words
        THEN all invalid words should be tracked and the valid words accepted
        """
        game_runner._initialize_game()
        game_runner._current_turn_number = 1

        json_responses = [
            '{"reasoning": "First guess", "guess": "ZXXCV"}',  # Invalid
            '{"reasoning": "First guess retry", "guess": "STARE"}',  # Valid - completes guess 1
            '{"reasoning": "Second guess", "guess": "QWERT"}',  # Invalid
            '{"reasoning": "Second guess retry", "guess": "CRANE"}',  # Valid - completes guess 2
        ]

        with patch.object(llm_client, "generate_response", side_effect=json_responses):
            game_runner._make_guess_attempt()  # First guess
            game_runner._make_guess_attempt()  # Second guess

        assert game_runner.game.guesses == ["STARE", "CRANE"]
        assert len(game_runner.invalid_word_attempts) == 2
        invalid_words = [attempt["word"] for attempt in game_runner.invalid_word_attempts]
        assert "ZXXCV" in invalid_words
        assert "QWERT" in invalid_words

    def test_invalid_word_max_retries_exceeded(self, game_runner, llm_client):
        """
        GIVEN a GameRunner with an initialized game
        WHEN the LLM exceeds max retries for invalid words
        THEN a descriptive error should be raised
        """
        game_runner._initialize_game()

        # Mock LLM to always return invalid words (exceeds MAX_INVALID_WORD_RETRIES)
        json_response = '{"reasoning": "Invalid word", "guess": "ZXXCV"}'
        with patch.object(llm_client, "generate_response", return_value=json_response):
            with pytest.raises(ValueError, match="Could not get valid word from LLM after 5 attempts"):
                game_runner._make_guess_attempt()

        # Should have tracked all invalid attempts
        assert len(game_runner.invalid_word_attempts) == game_runner.MAX_INVALID_WORD_ATTEMPTS

    def test_parsing_error_retry_success(self, game_runner, llm_client):
        """
        GIVEN a GameRunner with an initialized game
        WHEN the LLM first returns unparseable response, then valid JSON
        THEN the parsing error should be retried and the valid response accepted
        """
        game_runner._initialize_game()

        # Mock LLM responses: first unparseable, then valid JSON
        llm_responses = [
            "I think the word is STARE but I can't format it properly",  # Unparseable
            '{"reasoning": "Trying a common word", "guess": "STARE"}',  # Valid JSON
        ]

        with patch.object(llm_client, "generate_response", side_effect=llm_responses):
            game_runner._make_guess_attempt()

        # Should have made the valid guess
        assert game_runner.game.guesses[-1] == "STARE"
        assert game_runner.game.guess_reasoning[-1] == "Trying a common word"

    def test_parsing_error_max_retries_exceeded(self, game_runner, llm_client):
        """
        GIVEN a GameRunner with an initialized game
        WHEN the LLM exceeds max retries for parsing errors
        THEN a descriptive error should be raised
        """
        game_runner._initialize_game()

        # Mock LLM to always return unparseable responses (exceeds MAX_PARSING_RETRIES)
        llm_responses = [
            "I think STARE",
            "The word is probably CRANE",
            "Let me try WORLD this time",
            "And again",
            "And again again",
            "And one more",
        ]

        with patch.object(llm_client, "generate_response", side_effect=llm_responses):
            with pytest.raises(ValueError, match="Could not parse valid guess from LLM response after 5 attempts"):
                game_runner._make_guess_attempt()

    def test_mixed_parsing_and_invalid_word_retries(self, game_runner, llm_client):
        """
        GIVEN a GameRunner with an initialized game
        WHEN the LLM has both parsing errors and invalid words
        THEN both should be retried independently, and success should be achieved
        """
        game_runner._initialize_game()
        game_runner._current_turn_number = 1

        # Mock LLM responses: parsing error, then invalid word, then success
        llm_responses = [
            "I think the word is STARE",  # Parsing error
            '{"reasoning": "Trying random", "guess": "ZXXCV"}',  # Invalid word
            '{"reasoning": "Trying real word", "guess": "STARE"}',  # Success
        ]

        with patch.object(llm_client, "generate_response", side_effect=llm_responses):
            game_runner._make_guess_attempt()

        # Should have made the valid guess
        assert game_runner.game.guesses[-1] == "STARE"

        # Should have tracked the invalid word attempt
        assert len(game_runner.invalid_word_attempts) == 1
        assert game_runner.invalid_word_attempts[0]["word"] == "ZXXCV"

    def test_prompt_feedback_with_invalid_words(self, game_runner):
        """
        GIVEN a GameRunner with invalid word attempts tracked
        WHEN generating a prompt with feedback
        THEN the prompt should include information about invalid words
        """
        game_runner._initialize_game()
        game_runner.invalid_word_attempts = [
            {"word": "ZXXCV", "turn_number": 1, "attempt_number": 1},
            {"word": "QWERT", "turn_number": 2, "attempt_number": 1},
        ]

        prompt = game_runner._generate_prompt()

        # Should contain feedback about invalid words
        assert "NOTE: The following words you tried are not in the dictionary" in prompt
        assert "ZXXCV, QWERT" in prompt

    def test_prompt_feedback_no_invalid_words(self, game_runner):
        """
        GIVEN a GameRunner with no invalid word attempts
        WHEN generating a prompt with feedback
        THEN the prompt should not include invalid word feedback
        """
        game_runner._initialize_game()
        game_runner.invalid_word_attempts = []

        original_prompt = game_runner.prompt_template.format_prompt(game_runner.game.get_game_state())
        feedback_prompt = game_runner._generate_prompt()

        # Should be identical to the original prompt
        assert feedback_prompt == original_prompt
        assert "not valid English words" not in feedback_prompt

    def test_complete_game_with_retries_tracked_in_metadata(self, game_runner, llm_client):
        """
        GIVEN a GameRunner that encounters invalid words during gameplay
        WHEN running a complete game
        THEN the final result should track all invalid word attempts in metadata
        """
        # Mock responses that include invalid words
        json_responses = [
            '{"reasoning": "First try", "guess": "ZXXCV"}',  # Invalid
            '{"reasoning": "Second try", "guess": "STARE"}',  # Valid
            '{"reasoning": "Final guess", "guess": "CRANE"}',  # Winning guess
        ]

        with patch.object(llm_client, "generate_response", side_effect=json_responses):
            result = game_runner.run_complete_game()

        # Should have completed successfully
        assert result.success is True
        assert result.game_state.won is True

        # Invalid attempts count tracked in metadata (words stored in database)
        assert hasattr(result.metadata, "total_invalid_attempts")
        assert result.metadata.total_invalid_attempts == 1
