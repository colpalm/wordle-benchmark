import sys
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from utils.logging_config import configure_logging, get_logger
from wordle.game_runner import GameRunner
from wordle.word_list import WordList
from wordle.prompt_templates import PromptTemplateFactory
from wordle.response_parser import ResponseParserFactory
from llm_integration.llm_client import LLMClient, LLMError

logger = get_logger(__name__)


# Helper fixtures and mocks
@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = Mock(spec=LLMClient)
    client.get_model_name.return_value = "test-model"
    client.generate_response.return_value = "CRANE"
    return client


@pytest.fixture
def mock_template():
    """Create a mock prompt template."""
    template = Mock()
    template.get_template_name.return_value = "test-template"
    template.format_prompt.return_value = "Test prompt"
    return template


@pytest.fixture
def mock_parser():
    """Create a mock response parser."""
    parser = Mock()
    parser.get_parser_name.return_value = "test-parser"
    parser.extract_guess.return_value = "CRANE"
    parser.extract_reasoning.return_value = "Test reasoning"
    return parser


@pytest.fixture
def game_runner(word_list, mock_llm_client, mock_template, mock_parser):
    """Create a GameRunner instance with mocked dependencies."""
    return GameRunner(
        word_list=word_list,
        llm_client=mock_llm_client,
        prompt_template=mock_template,
        response_parser=mock_parser,
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