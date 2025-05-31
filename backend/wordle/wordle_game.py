from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from wordle.enums import GameStatus, LetterStatus


class WordleGame:
    """
    Core Wordle Game Logic with NYT API integration
    """

    WORD_LENGTH = 5
    MAX_GUESSES = 6
    NYT_API_URL = "https://www.nytimes.com/svc/wordle/v2"
    VALID_WORDS_FILE = "wordle-valid-words.txt"
    RESOURCES_DIR = Path(__file__).parent / "resources"

    _valid_words: Optional[set[str]] = None

    @classmethod
    def _get_valid_words(cls) -> set[str]:
        """Loads valid words if not already loaded, then returns them."""
        if cls._valid_words is None:
            print("Loading valid words for the first time...")
            cls._valid_words = cls._load_valid_words_from_file(cls.RESOURCES_DIR / cls.VALID_WORDS_FILE)
        return cls._valid_words

    @property
    def valid_words(self) -> set[str]:
        """
        Property to access class-level valid words

        Note: Returns a reference to the shared set - mutations affect all instances.
        Use self.valid_words.add() to modify.
        """
        return WordleGame._get_valid_words()

    def __init__(self, target_word: Optional[str] = None, date: Optional[str] = None):
        """
        Initialize Wordle game.

        Args:
            target_word (str): Specific word to use (mainly for testing). If None, fetches from NYT API
            date (str): Date in YYYY-MM-DD format. If None, uses today's date
        """

        self.guesses: list[str] = []
        self.guess_results: list[list[dict]] = []
        self.status = GameStatus.IN_PROGRESS

        if target_word:
            self.target_word = target_word.upper()
        else:
            self.target_word = self._fetch_daily_word(date).upper()

        # Since we're not using the official NYT valid word list, we need to ensure the target word is in our valid word list
        self._ensure_target_is_valid()

    @staticmethod
    def _load_valid_words_from_file(word_list_path: Path) -> set[str]:
        """
        Load valid words from a file

        Args:
            word_list_path: Path to the word list file
        Returns:
            Set of valid 5-letter words
        Raises:
            FileNotFoundError: If the word list file doesn't exist
            ValueError: If no valid words are found in the file
            RuntimeError: If there's an error reading/parsing the file
        """
        valid_words = set()

        try:
            with open(word_list_path, "r", encoding='utf-8') as f:
                for line in f:
                    word = line.strip().upper()
                    if len(word) == WordleGame.WORD_LENGTH and word.isalpha():
                        valid_words.add(word)

            if not valid_words:
                raise ValueError(f"No valid words found in the {word_list_path}")

            print(f"Loaded {len(valid_words)} valid words from {word_list_path}")
            return valid_words

        except FileNotFoundError:
            raise FileNotFoundError(f"Word list file not found: {word_list_path.absolute()}")
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Error loading word list from '{word_list_path}': {e}")

    def _ensure_target_is_valid(self) -> None:
        """Ensure the target word is in our valid word list. Add it if not."""
        if not self.valid_words:
            return

        if self.target_word not in self.valid_words:
            print(f"Warning: Target word '{self.target_word}' not in valid words list. Adding it to ensure winnability.")
            self.valid_words.add(self.target_word)
            # TODO: Add fucntionality to log added words and make them available for future games
            # self._log_added_word(self.target_word)
        else:
            print(f"Target word '{self.target_word}' is valid.")

    def _fetch_daily_word(self, date: Optional[str]) -> str:
        """Fetch today's Wordle solution from NYT API"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        url = f"{self.NYT_API_URL}/{date}.json"

        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            solution = data.get("solution")
            if not solution:
                raise ValueError("No solution found in API response")

            return solution

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch Wordle solution from NYT API: {e}")

    def _evaluate_guess(self, guess: str) -> list[dict]:
        """
        Evaluate a guess against the target word

        Returns a list of letter evaluations with position, letter, and status
        """
        guess = guess.upper()
        result = []

        # Count available letters in the target
        target_letter_counts = {}
        for letter in self.target_word:
            target_letter_counts[letter] = target_letter_counts.get(letter, 0) + 1

        # First Pass: Mark correct positions
        temp_result = [None] * self.WORD_LENGTH

        for i, letter in enumerate(guess):
            if letter == self.target_word[i]:
                temp_result[i] = {
                    "position": i,
                    "letter": letter,
                    "status": LetterStatus.CORRECT.value,
                }
                target_letter_counts[letter] -= 1

        # Second Pass: Mark present (yellow) and absent (gray) letters
        for i, letter in enumerate(guess):
            if temp_result[i] is not None:
                # Already marked as correct
                result.append(temp_result[i])
            elif letter in target_letter_counts and target_letter_counts[letter] > 0:
                # Letter is present but in the wrong position (yellow)
                result.append({
                    "position": i,
                    "letter": letter,
                    "status": LetterStatus.PRESENT.value,
                })
                target_letter_counts[letter] -= 1
            else:
                # Letter is absent (gray)
                result.append({
                    "position": i,
                    "letter": letter,
                    "status": LetterStatus.ABSENT.value
                })

        return result

    def make_guess(self, guess: str) -> dict:
        """
        Make a guess and returns the result
        Args:
            guess: 5-letter word guess
        Returns:
            Dict containing guess result and game status
        """
        if self.status != GameStatus.IN_PROGRESS:
            raise ValueError(f"Game is not in progress (status: {self.status})")

        guess = guess.upper().strip()

        # Validate guess format
        is_valid, error_msg = self.validate_guess_format(guess)
        if not is_valid:
            raise ValueError(error_msg)

        # Validate guess against valid words
        if guess not in self.valid_words:
            raise ValueError("Guess must be a valid English word")

        guess_result = self._evaluate_guess(guess)
        self.guesses.append(guess)
        self.guess_results.append(guess_result)

        # Check game status
        if guess == self.target_word:
            self.status = GameStatus.WON
        elif len(self.guesses) == self.MAX_GUESSES:
            self.status = GameStatus.LOST

        return {
            "guess": guess,
            "result": guess_result,
            "status": self.status.value,
            "guesses_remaining": self.MAX_GUESSES - len(self.guesses),
            "target_word": self.target_word if self.status != GameStatus.IN_PROGRESS else None # Hidden from LLM during gameplay
        }

    def get_game_state(self) -> dict:
        """Get current game state"""
        return {
            "status": self.status.value,
            "guesses": self.guesses,
            "guess_results": self.guess_results,
            "guesses_made": len(self.guesses),
            "guesses_remaining": self.MAX_GUESSES - len(self.guesses),
            "target_word": self.target_word if self.status != GameStatus.IN_PROGRESS else None, # Hidden from LLM during gameplay
            "won": self.status == GameStatus.WON,
            "game_over": self.status != GameStatus.IN_PROGRESS,
        }

    @staticmethod
    def validate_guess_format(input_guess: str) -> tuple[bool, str]:
        """
        Validate that a guess meets basic format requirements - str, length, and alphabetical characters only.

        Args:
            input_guess: The extracted guess to validate

        Returns:
            True and empty string if the guess is a valid format, False otherwise with a message explaining the error
        """
        if not isinstance(input_guess, str):
            return False, "Guess must be a string"
        if len(input_guess) != WordleGame.WORD_LENGTH:
            return False, f"Guess must be a {WordleGame.WORD_LENGTH}-letter word"
        if not input_guess.isalpha():
            return False, "Guess must only contain alphabetical characters"
        return True, ""


# Example usage and testing
if __name__ == "__main__":
    # Test with a known word
    print("=== Testing with known word 'CRANE' ===")
    game = WordleGame(target_word="CRANE")

    test_guesses = ["STARE", "CRANE"]

    for guess in test_guesses:
        try:
            result = game.make_guess(guess)
            print(f"\nGuess: {guess}")
            print(f"Status: {result['status']}")
            print("Letter results:")
            for letter_result in result['result']:
                print(f"  {letter_result['letter']} at position {letter_result['position']}: {letter_result['status']}")

            if result['status'] != 'in_progress':
                print(f"\nGame Over! Target word was: {result['target_word']}")
                break

        except Exception as e:
            print(f"Error making guess '{guess}': {e}")
