from datetime import datetime
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
        self.valid_words: set() # TODO: Where to get this, NYT as well?

        if target_word:
            self.target_word = target_word.upper()
        else:
            self.target_word = self._fetch_daily_word(date).upper()


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

        # TODO: Add valid word validation when we have the word list
        # if guess not in self.valid_words:
        #     raise ValueError("Guess must be a valid English word")

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
