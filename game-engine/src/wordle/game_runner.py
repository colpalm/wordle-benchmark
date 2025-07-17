import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from database.service import GameDatabaseService
from llm_integration.llm_client import LLMClient
from llm_integration.openrouter_client import OpenRouterClient
from utils.logging_config import get_logger
from wordle.enums import GameStatus, LetterStatus
from wordle.models import GameResult, GameState, GameMetadata, LetterResult
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

    MAX_INVALID_WORD_ATTEMPTS = 5  # How many attempts for invalid words per guess
    MAX_PARSING_ATTEMPTS = 5       # How many attempts for parsing failures per guess

    def __init__(
            self,
            word_list: WordList,
            llm_client: LLMClient,
            prompt_template: PromptTemplate,
            response_parser: ResponseParser,
            target_word: Optional[str] = None,
            date: Optional[str] = None,
            db_service: Optional[GameDatabaseService] = None
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
            db_service: Optional database service for persisting results
        """
        self.word_list = word_list
        self.llm_client = llm_client
        self.prompt_template = prompt_template
        self.response_parser = response_parser
        self.target_word = target_word
        self.date = date
        self.db_service = db_service

        # Game state
        self.game: WordleGame | None = None
        self.start_time: datetime | None = None

        # Track retry information for this game session (all invalid words tried)
        self.invalid_word_attempts: list[str] = []
        
        # Track LLM interactions for database persistence
        self.llm_interactions: list[dict[str, Any]] = []
        self._current_interaction: dict[str, Any] | None = None
        self._current_turn_number: int = 0

    def run_complete_game(self) -> GameResult:
        """
        Run a complete Wordle game from start to finish.

        Returns:
            GameResult with game state and metadata
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
        while self.game.status == GameStatus.IN_PROGRESS and self._current_turn_number < WordleGame.MAX_GUESSES:
            self._current_turn_number += 1
            logger.info(f"\n--- Guess {self._current_turn_number}/{WordleGame.MAX_GUESSES} ---")

            try:
                self._make_guess_attempt()

            except Exception as e:
                logger.error(f"💥 Failed to make guess {self._current_turn_number}: {e}")
                raise

    def _make_guess_attempt(self) -> None:
        """Make a guess attempt with retry logic for parsing and invalid word errors."""
        attempt_state = {"parsing": 1, "invalid_word": 1}

        while True:
            prompt = self._generate_prompt()
            logger.debug(f"Generated prompt:\n{prompt}")

            raw_response = self._get_llm_response(prompt)
            self._initialize_interaction_data(prompt, raw_response)

            # Try to parse the response
            guess, reasoning = self._try_parse_with_retry(raw_response, attempt_state)
            if guess is None:  # Parsing failed, try again with new response
                continue

            # Try to execute the guess
            success = self._try_execute_guess_with_retry(guess, reasoning, attempt_state)
            if success:
                return

    def _get_llm_response(self, prompt: str) -> str:
        """Get response from LLM."""
        logger.debug("Requesting LLM response...")
        raw_response = self.llm_client.generate_response(prompt)
        logger.debug(f"Raw response: '{raw_response}'")
        return raw_response
    
    def _initialize_interaction_data(self, prompt: str, raw_response: str) -> None:
        """Initialize interaction data for database persistence."""
        # Get usage stats and add additional fields for database
        interaction_data = self.llm_client.get_current_usage_stats()
        interaction_data.update({
            "prompt_text": prompt,
            "raw_response": raw_response
        })
        
        # Store for completion after parsing
        self._current_interaction = interaction_data

    def _generate_prompt(self) -> str:
        """Generate prompt with feedback about invalid words (if needed)."""
        # Get the current game state for prompt
        game_state = self.game.get_game_state()

        # Generate base prompt
        prompt = self.prompt_template.format_prompt(game_state)

        # Add invalid word feedback if we have any
        if self.invalid_word_attempts:
            invalid_list = ", ".join(self.invalid_word_attempts)
            feedback = f"Invalid Guesses:\nNOTE: The following words you tried are not in the dictionary: {invalid_list}\n\n"

            prompt = self.prompt_template.insert_feedback(prompt, feedback)

        return prompt

    def _try_parse_with_retry(self, raw_response: str, attempt_state: dict) -> tuple[Optional[str], Optional[str]]:
        """Try to parse response, handle retries, return None if failed after max retries."""
        try:
            result = self._parse_llm_response(raw_response)
            # Capture successful parsing
            if self._current_interaction:
                self._current_interaction.update({
                    "parse_success": True,
                    "attempt_number": attempt_state["parsing"]
                })
            return result
        except ValueError as parse_error:
            # Capture failed parsing
            if self._current_interaction:
                self._current_interaction.update({
                    "parse_success": False,
                    "parse_error_message": str(parse_error),
                    "attempt_number": attempt_state["parsing"]
                })
            
            if self._should_retry_parsing(attempt_state["parsing"], parse_error, raw_response):
                attempt_state["parsing"] += 1  # Increment for next attempt
                return None, None  # Signal to continue retry loop
            else:
                raise self._create_parsing_error(parse_error)

    def _try_execute_guess_with_retry(self, guess: str, reasoning: Optional[str], attempt_state: dict) -> bool:
        """Try to execute guess, handle retries, return True if successful."""
        try:
            self._execute_game_guess(guess, reasoning)
            # Complete and save the interaction data
            self._finalize_current_interaction()
            return True  # Success!
        except ValueError as game_error:
            return self._handle_game_error(game_error, guess, attempt_state)

    def _parse_llm_response(self, raw_response: str) -> tuple[str, Optional[str]]:
        """Parse LLM response to extract guess and reasoning."""
        guess = self.response_parser.extract_guess(raw_response)
        reasoning = self.response_parser.extract_reasoning(raw_response)

        logger.info(f"Extracted guess: {guess}")
        if reasoning:
            logger.info(f"LLM reasoning: {reasoning}")

        return guess, reasoning

    def _should_retry_parsing(self, parsing_attempts: int, parse_error: ValueError, raw_response: str) -> bool:
        """Check if we should retry parsing and log appropriately."""
        if parsing_attempts < self.MAX_PARSING_ATTEMPTS:
            logger.warning(
                f"Failed to parse response (attempt {parsing_attempts}/{self.MAX_PARSING_ATTEMPTS}): {parse_error}")
            logger.debug(f"Problematic response: '{raw_response}'")
            return True
        return False

    def _create_parsing_error(self, parse_error: ValueError) -> ValueError:
        """Create error for parsing failure after max attempts."""
        logger.error(f"Failed to parse response after {self.MAX_PARSING_ATTEMPTS} attempts")
        return ValueError(
            f"Could not parse valid guess from LLM response after {self.MAX_PARSING_ATTEMPTS} attempts: {parse_error}")

    def _execute_game_guess(self, guess: str, reasoning: Optional[str]) -> None:
        """Execute the guess in the game and log results."""
        game_results = self.game.make_guess(guess, reasoning)
        GameRunner._log_guess_result(game_results)

    @staticmethod
    def _is_invalid_word_error(game_error: ValueError) -> bool:
        """Check if the error is specifically an invalid word error."""
        return "valid English word" in str(game_error)

    def _should_retry_invalid_word(self, invalid_word_attempts: int, guess: str) -> bool:
        """Check if we should retry invalid word and log appropriately."""
        if invalid_word_attempts < self.MAX_INVALID_WORD_ATTEMPTS:
            logger.warning(
                f"Invalid word '{guess}' (attempt {invalid_word_attempts}/{self.MAX_INVALID_WORD_ATTEMPTS}). Retrying...")
            return True
        return False

    def _create_invalid_word_error(self) -> ValueError:
        """Create error for invalid word failure after max attempts."""
        logger.error(f"Failed to get valid word after {self.MAX_INVALID_WORD_ATTEMPTS} attempts")
        invalid_words_list = ", ".join(self.invalid_word_attempts)
        return ValueError(
            f"Could not get valid word from LLM after {self.MAX_INVALID_WORD_ATTEMPTS} attempts. Invalid words tried: {invalid_words_list}")

    def _handle_game_error(self, game_error: ValueError, guess: str, attempt_state: dict) -> bool:
        """Handle game errors, return True if should continue, False if should retry, raises if failed."""
        if GameRunner._is_invalid_word_error(game_error):
            # Handle invalid word
            self.invalid_word_attempts.append(guess)

            if self._should_retry_invalid_word(attempt_state["invalid_word"], guess):
                attempt_state["invalid_word"] += 1  # Increment for next attempt
                return False  # Signal to continue retry loop
            else:
                raise self._create_invalid_word_error()
        else:
            raise game_error  # Re-raise non-invalid-word errors

    @staticmethod
    def _log_guess_result(result: dict[str, Any]) -> None:
        """Log the result of a guess in a readable format."""
        guess = result["guess"]
        status = result["status"]
        remaining = result["guesses_remaining"]

        logger.info(f"Guess: {guess}")
        logger.info(f"Status: {status.upper()}")
        logger.info(f"Guesses Remaining: {remaining}")

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

    def _create_result(self) -> GameResult:
        """Create the final game result."""
        if not self.game or not self.start_time:
            return self._create_error_result("Game not properly initialized")

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        game_state_dict = self.game.get_game_state()

        # Convert dictionary game state to Pydantic GameState
        game_state = self._convert_game_state_to_pydantic(game_state_dict)
        
        # Create metadata
        metadata = GameMetadata(
            model=self.llm_client.get_model_name(),
            template=self.prompt_template.get_template_name(),
            parser=self.response_parser.get_parser_name(),
            duration_seconds=duration,
            start_time=self.start_time,
            end_time=end_time,
            date=self.date or datetime.now().strftime("%Y-%m-%d"),
            invalid_word_attempts=self.invalid_word_attempts,
            total_invalid_attempts=len(self.invalid_word_attempts)
        )

        # Log final summary
        self._log_game_summary(game_state_dict, duration)

        result = GameResult(
            success=True,
            game_state=game_state,
            metadata=metadata
        )
        
        # Save to database if service is provided
        if self.db_service:
            try:
                self.db_service.save_game_result(result, self.llm_interactions)
                logger.debug("Game result saved to database")
            except Exception as e:
                logger.warning(f"Failed to save game result to database: {e}")
        
        return result

    def _convert_game_state_to_pydantic(self, game_state_dict: dict) -> GameState:
        """Convert dictionary game state to Pydantic GameState model."""
        # Convert guess_results from list of list of dicts to list of list of LetterResult
        pydantic_guess_results = []
        for guess_result in game_state_dict["guess_results"]:
            letter_results = []
            for letter_dict in guess_result:
                letter_result = LetterResult(
                    position=letter_dict["position"],
                    letter=letter_dict["letter"],
                    status=LetterStatus(letter_dict["status"])
                )
                letter_results.append(letter_result)
            pydantic_guess_results.append(letter_results)
        
        # Handle target_word - it might be None during gameplay
        target_word = game_state_dict.get("target_word")
        if not target_word:
            # Game is still in progress, we need the actual target word for the model
            target_word = self.game.target_word
        
        return GameState(
            target_word=target_word,
            guesses=game_state_dict["guesses"],
            guess_reasoning=game_state_dict["guess_reasoning"],
            guess_results=pydantic_guess_results,
            guesses_made=game_state_dict["guesses_made"],
            guesses_remaining=game_state_dict["guesses_remaining"],
            status=GameStatus(game_state_dict["status"]),
            won=game_state_dict["won"],
            game_over=game_state_dict["game_over"]
        )

    def _create_error_result(self, error_message: str) -> GameResult:
        """Create error result when game fails."""
        end_time = datetime.now()
        duration = 0
        if self.start_time:
            duration = (end_time - self.start_time).total_seconds()

        # Create metadata
        metadata = GameMetadata(
            model=self.llm_client.get_model_name(),
            template=self.prompt_template.get_template_name(),
            parser=self.response_parser.get_parser_name(),
            duration_seconds=duration,
            start_time=self.start_time or end_time,  # Use end_time as fallback
            end_time=end_time,
            date=self.date or datetime.now().strftime("%Y-%m-%d"),
            invalid_word_attempts=self.invalid_word_attempts,
            total_invalid_attempts=len(self.invalid_word_attempts)
        )

        # TODO: save partial game results
        return GameResult(
            success=False,
            game_state=None,  # No valid game state for error cases
            metadata=metadata,
            error=error_message
        )

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

        # Log invalid word attempts if any
        if self.invalid_word_attempts:
            logger.info(
                f"Invalid words attempted: {', '.join(self.invalid_word_attempts)} ({len(self.invalid_word_attempts)} total)")

        logger.info("=" * 50)

    def _finalize_current_interaction(self) -> None:
        """Complete the current interaction data and add it to the interactions list."""
        if self._current_interaction:
            # Add turn number and any missing fields
            self._current_interaction.update({
                "turn_number": self._current_turn_number
            })
            
            # Add to the interactions list
            self.llm_interactions.append(self._current_interaction)
            
            # Clear the current interaction
            self._current_interaction = None

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


