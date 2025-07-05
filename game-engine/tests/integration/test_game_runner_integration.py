import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from llm_integration.openrouter_client import OpenRouterClient
from utils.logging_config import get_logger
from wordle.enums import LetterStatus
from wordle.game_runner import GameRunner
from wordle.prompt_templates import PromptTemplateFactory
from wordle.response_parser import ResponseParserFactory
from wordle.word_list import WordList

load_dotenv()
logger = get_logger(__name__)


@pytest.mark.integration
@pytest.mark.api_calls
@pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY required for end-to-end system tests"
)
class TestGameRunnerIntegration:
    """
    End-to-end integration tests for GameRunner with real APIs.

    These tests make actual API calls to:
    - NYT Wordle API (for daily word)
    - OpenRouter/LLM API (for game responses)

    Not run in the normal test suite - used for debugging production issues.
    """

    @pytest.fixture
    def word_list(self):
        """Create WordList with real word files."""
        base_dir = Path(__file__).parent.parent.parent / "src" / "wordle"
        return WordList(
            base_valid_words_path=base_dir / "resources" / "wordle-valid-words.txt",
            added_valid_words_path=base_dir / "resources" / "added_valid_words.log"
        )

    @pytest.fixture
    def llm_client(self):
        """Create real LLM client with free model."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        # Using free Llama model - good instruction following for Wordle
        return OpenRouterClient(api_key=api_key, model="meta-llama/llama-3.3-70b-instruct:free")

    @pytest.fixture
    def template(self):
        """Create JSON template for structured responses."""
        return PromptTemplateFactory.create_template("json")

    @pytest.fixture
    def parser(self):
        """Create JSON parser to match template."""
        return ResponseParserFactory.create_parser("json")

    def test_complete_game_end_to_end(self, word_list, llm_client, template, parser):
        """
        GIVEN I have a GameRunner with real API clients
        WHEN I run a complete game with real NYT word and LLM calls
        THEN the game should complete successfully with valid results

        This test validates:
        - NYT API integration (fetches real daily word)
        - LLM API integration (makes real model calls)
        - Complete game flow from start to finish
        - All component integration working together
        """
        logger.info("🚀 Starting end-to-end integration test")
        logger.info(f"Model: {llm_client.get_model_name()}")
        logger.info(f"Template: {template.get_template_name()}")
        logger.info(f"Parser: {parser.get_parser_name()}")

        # Use a fixed historical date for predictable testing
        test_date = "2024-01-15"

        # Create GameRunner with real components
        game_runner = GameRunner(
            word_list=word_list,
            llm_client=llm_client,
            prompt_template=template,
            response_parser=parser,
            date=test_date  # Fixed date for consistency
        )

        # Makes real API calls
        result = game_runner.run_complete_game()

        # Assert successful completion
        assert result["success"] is True, f"Game failed: {result.get('error', 'Unknown error')}"

        # Assert game structure
        game_state = result["game_state"]
        assert game_state["game_over"] is True
        assert game_state["target_word"] is not None
        assert len(game_state["target_word"]) == 5
        assert game_state["target_word"].isalpha()
        assert game_state["target_word"].isupper()

        # Assert a valid number of guesses
        assert 1 <= len(game_state["guesses"]) <= 6
        assert game_state["guesses_made"] == len(game_state["guesses"])
        assert game_state["guesses_remaining"] == 6 - len(game_state["guesses"])

        # Assert all guesses are valid format
        for guess in game_state["guesses"]:
            assert len(guess) == 5
            assert guess.isalpha()
            assert guess.isupper()

        # Assert reasoning was captured for all guesses
        assert len(game_state["guess_reasoning"]) == len(game_state["guesses"])
        assert all(reasoning is not None for reasoning in game_state["guess_reasoning"])
        assert all(isinstance(reasoning, str) for reasoning in game_state["guess_reasoning"])
        assert all(len(reasoning.strip()) > 0 for reasoning in game_state["guess_reasoning"])

        # Assert guess results structure
        assert len(game_state["guess_results"]) == len(game_state["guesses"])
        for guess_result in game_state["guess_results"]:
            assert len(guess_result) == 5  # 5 letters per guess
            for letter_result in guess_result:
                assert "letter" in letter_result
                assert "position" in letter_result
                assert "status" in letter_result
                assert letter_result["status"] in [status.value for status in LetterStatus]

        # Assert metadata
        metadata = result["metadata"]
        assert metadata["model"] == llm_client.get_model_name()
        assert metadata["template"] == template.get_template_name()
        assert metadata["parser"] == parser.get_parser_name()
        assert metadata["date"] == test_date
        assert metadata["duration_seconds"] > 0
        assert metadata["start_time"] is not None
        assert metadata["end_time"] is not None

        # Log final results for debugging
        outcome = "WON" if game_state["won"] else "LOST"
        logger.info(f"🎯 Integration test completed: {outcome}")
        logger.info(f"Target word was: {game_state['target_word']}")
        logger.info(f"Completed in {len(game_state['guesses'])}/{6} guesses")
        logger.info(f"Duration: {metadata['duration_seconds']:.1f}s")

        logger.info("✅ End-to-end integration test PASSED")

    def test_game_runner_with_custom_target_word(self, word_list, llm_client, template, parser):
        """
        GIVEN I have a GameRunner with a custom target word
        WHEN I run a complete game (no NYT API call needed)
        THEN the game should complete successfully

        This test validates LLM integration without NYT API dependency.
        """
        logger.info("🎯 Testing with custom target word")

        # Using a simple target word that's likely to be guessed quickly
        game_runner = GameRunner(
            word_list=word_list,
            llm_client=llm_client,
            prompt_template=template,
            response_parser=parser,
            target_word="GLOBE"  # Common word
        )

        result = game_runner.run_complete_game()

        # Basic assertions - focused on LLM integration
        assert result["success"] is True
        assert result["game_state"]["target_word"] == "GLOBE"
        assert result["game_state"]["game_over"] is True
        assert 1 <= len(result["game_state"]["guesses"]) <= 6

        outcome = "WON" if result["game_state"]["won"] else "LOST"
        logger.info(f"🎯 Custom target test completed: {outcome} with {len(result['game_state']['guesses'])} guesses")