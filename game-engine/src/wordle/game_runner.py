import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from llm_integration.llm_client import LLMClient
from llm_integration.openrouter_client import OpenRouterClient
from utils.logging_config import get_logger
from wordle.enums import GameStatus
from wordle.prompt_templates import PromptTemplate, PromptTemplateFactory
from wordle.response_parser import ResponseParser, ResponseParserFactory
from wordle.word_list import WordList
from wordle.wordle_game import WordleGame

logger = get_logger(__name__)


class GameRunner:
    """
    GameRunner that orchestrates a complete Wordle game session.
    """

    MODELS_TO_RUN = ["openai/gpt-4o-mini",
                     "openai/o3",
                     "anthropic/claude-sonnet-4",
                     "anthropic/claude-opus-4",
                     "google/gemini-2.5-flash",
                     "google/gemini-2.5-pro"]

    def __init__(
            self,
            word_list: WordList,
            llm_client: LLMClient,
            prompt_template: PromptTemplate,
            response_parser: ResponseParser,
            target_word: Optional[str] = None,
            date: Optional[str] = None
    ):
        """
        Initialize GameRunner with required components.

        Args:
            word_list: WordList instance for valid word checking
            llm_client: LLM client for generating responses
            prompt_template: Template for formatting prompts
            response_parser: Parser for extracting guesses from LLM responses
            target_word: Specific target word (if None, fetches from NYT API)
            date: Date for word fetch (if None, uses today)
        """
        self.word_list = word_list
        self.llm_client = llm_client
        self.prompt_template = prompt_template
        self.response_parser = response_parser
        self.target_word = target_word
        self.date = date

        # Game state
        self.game: WordleGame | None = None
        self.start_time: datetime | None = None

    def run_complete_game(self) -> dict[str, Any]:
        """
        Run a complete Wordle game from start to finish.

        Returns:
            Dictionary with game results and metadata
        """
        logger.info("Starting Wordle game")
        logger.info(f"Model: {self.llm_client.get_model_name()}")
        logger.info(f"Template: {self.prompt_template.get_template_name()}")
        logger.info(f"Parser: {self.response_parser.get_parser_name()}")

        self.start_time = datetime.now()

        try:
            self._initialize_game()
            self._play_game()

            return self._create_result()

        except Exception as e:
            logger.error(f"Game failed: {e}")
            return self._create_error_result(str(e))

    def _initialize_game(self) -> None:
        """Initialize the Wordle game with the target word."""
        self.game = WordleGame(
            word_list=self.word_list,
            target_word=self.target_word,
            date=self.date
        )

        if self.target_word:
            logger.info("Using custom target word")
            logger.debug(f"Target: {self.target_word}")
        else:
            logger.info(f"Using daily word for {self.date or 'today'}")

    def _play_game(self) -> None:
        """Play the complete game loop."""
        guess_number = 1

        while self.game.status == GameStatus.IN_PROGRESS and guess_number <= WordleGame.MAX_GUESSES:
            logger.info(f"\n--- Guess {guess_number}/{WordleGame.MAX_GUESSES} ---")

            try:
                # Make a single guess attempt
                self._make_guess_attempt()
                guess_number += 1

            except Exception as e:
                logger.error(f"💥 Failed to make guess {guess_number}: {e}")
                # TODO: Currently failing fast - add retry logic
                raise

    def _make_guess_attempt(self) -> None:
        """Make a single guess attempt."""
        # Get the current game state for prompt
        game_state = self.game.get_game_state()

        # Generate prompt
        prompt = self.prompt_template.format_prompt(game_state)

        # Get LLM response
        logger.debug("Requesting LLM response...")
        start_time = time.time()
        raw_response = self.llm_client.generate_response(prompt)
        response_time = time.time() - start_time

        logger.debug(f"LLM response time: {response_time:.2f}s")
        logger.debug(f"Raw response: '{raw_response}'")

        # Parse the response
        guess = self.response_parser.extract_guess(raw_response)
        reasoning = self.response_parser.extract_reasoning(raw_response)

        logger.info(f"Extracted guess: {guess}")
        if reasoning:
            logger.info(f"LLM reasoning: {reasoning}")

        # Make the guess in the game
        game_results = self.game.make_guess(guess, reasoning)

        # Log the result
        GameRunner._log_guess_result(game_results)

    @staticmethod
    def _log_guess_result(result: dict[str, Any]) -> None:
        """Log the result of a guess in a readable format."""
        guess = result["guess"]
        status = result["status"]
        remaining = result["guesses_remaining"]

        logger.info(f"Guess: {guess}")
        logger.info(f"Status: {status.upper()}")
        logger.info(f"Remaining: {remaining}")

        # Create the emoji feedback line
        feedback_line = ""
        for letter_result in result["result"]:
            letter = letter_result["letter"]
            letter_status = letter_result["status"]

            if letter_status == "correct":
                feedback_line += f"🟩{letter}"
            elif letter_status == "present":
                feedback_line += f"🟨{letter}"
            else:  # absent
                feedback_line += f"⬛{letter}"

        logger.info(f"Result: {feedback_line}")

    def _create_result(self) -> dict[str, Any]:
        """Create the final game result."""
        if not self.game or not self.start_time:
            return self._create_error_result("Game not properly initialized")

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        game_state = self.game.get_game_state()

        # Log final summary
        self._log_game_summary(game_state, duration)

        return {
            "success": True,
            "game_state": game_state,
            "metadata": {
                "model": self.llm_client.get_model_name(),
                "template": self.prompt_template.get_template_name(),
                "parser": self.response_parser.get_parser_name(),
                "duration_seconds": duration,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "date": self.date or datetime.now().strftime("%Y-%m-%d")
            }
        }

    def _create_error_result(self, error_message: str) -> dict[str, Any]:
        """Create error result when game fails."""
        end_time = datetime.now()
        duration = 0
        if self.start_time:
            duration = (end_time - self.start_time).total_seconds()

        return {
            "success": False,
            "error": error_message,
            "metadata": {
                "model": self.llm_client.get_model_name(),
                "template": self.prompt_template.get_template_name(),
                "parser": self.response_parser.get_parser_name(),
                "duration_seconds": duration,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": end_time.isoformat(),
                "date": self.date or datetime.now().strftime("%Y-%m-%d")
            }
        }

    def _log_game_summary(self, game_state: dict[str, Any], duration: float) -> None:
        """Log a summary of the completed game."""
        logger.info("\n" + "=" * 50)
        logger.info("GAME COMPLETE")
        logger.info("=" * 50)

        if game_state["won"]:
            logger.info(f"VICTORY! Solved in {game_state['guesses_made']}/{WordleGame.MAX_GUESSES} guesses")
        else:
            logger.info(f"DEFEAT after {WordleGame.MAX_GUESSES} guesses")

        logger.info(f"Target word: {game_state['target_word']}")
        logger.info(f"Duration: {duration:.1f}s")
        logger.info(f"Model: {self.llm_client.get_model_name()}")

        logger.info("\n📝 Guess sequence:")
        for i, (guess, reasoning) in enumerate(zip(game_state["guesses"], game_state["guess_reasoning"])):
            reasoning_text = reasoning or "No reasoning"
            logger.info(f"  {i + 1}. {guess} - {reasoning_text}")

        logger.info("=" * 50)

if __name__ == "__main__":
    # Setup file paths with env var support
    BASE_DIR = Path(__file__).parent
    DEFAULT_WORDS_FILE = BASE_DIR / "resources" / "wordle-valid-words.txt"
    DEFAULT_LOG_FILE = BASE_DIR / "resources" / "added_valid_words.log"

    word_list = WordList(
        base_valid_words_path=Path(os.getenv("WORDLE_WORDS_FILE", DEFAULT_WORDS_FILE)),
        added_valid_words_path=Path(os.getenv("WORDLE_LOG_FILE", DEFAULT_LOG_FILE))
    )

    # Setup template/parser
    template = PromptTemplateFactory.create_template("json")
    parser = ResponseParserFactory.create_parser("json")
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("OPENROUTER_API_KEY environment variable is required")
        sys.exit(1)

    for model in GameRunner.MODELS_TO_RUN:
        try:
            llm_client = OpenRouterClient(api_key=os.getenv("OPENROUTER_API_KEY"), model=model)

            runner = GameRunner(word_list, llm_client, template, parser)
            result = runner.run_complete_game()
        except Exception as e:
            print(f"{model} failed: {e}")
            # Continue with the next model instead of crashing
            continue


