from datetime import datetime
from pathlib import Path
from typing import Optional

from utils.logging_config import get_logger

logger = get_logger(__name__)


class WordList:
    """
    Manages the collection of valid Wordle words, including loading from files and
    adding new words during gameplay if needed.
    """

    WORD_LENGTH = 5

    def __init__(self, base_valid_words_path: Path, added_valid_words_path: Path):
        """
        Initialize WordList with file paths for base words and added word log.
        Args:
            base_valid_words_path: Path to the main word list file
            added_valid_words_path: Path to the log file for dynamically added words
        """
        self.base_valid_words_path = base_valid_words_path
        self.added_valid_words_path = added_valid_words_path
        self._words: Optional[set[str]] = None

    @property
    def words(self) -> set[str]:
        """
        Lazy-loaded set of all valid words (base and added).
        Returns a reference to the internal set - mutations affect all instances.
        """
        if self._words is None:
            logger.info("Loading valid words for the first time...")
            self._words = self._load_all_valid_words()
        return self._words

    def is_valid(self, word: str) -> bool:
        """Check if a word is in the valid word list."""
        return word.upper() in self.words

    def add_word(self, word: str) -> None:
        """
        Add a new word to the valid word list and log it.
        Args:
            word: The word to add (will be normalized to uppercase)
        """
        word = word.upper()

        # Basic defensive validation (word should be in valid format as this point)
        if not self._is_valid_word_format(word):
            raise ValueError(f"Invalid word format: '{word}' (must be {WordList.WORD_LENGTH} alphabetic characters)")

        if word not in self.words:
            # Add to an in-memory set
            self.words.add(word)
            # Log to file for persistence
            self._log_word(word)
            logger.info(f"Added new word '{word}' to valid words list.")

    def _load_all_valid_words(self) -> set[str]:
        """Load the complete set of valid words by combining base words and added words."""
        base_words = self._load_valid_words_from_file()
        added_words = self._load_added_valid_words_from_log()
        return base_words | added_words

    def _load_added_valid_words_from_log(self) -> set[str]:
        """Load previously added words from the log file."""
        if not self.added_valid_words_path.exists():
            return set()

        added_words = set()
        try:
            with open(self.added_valid_words_path, "r", encoding="utf-8") as f:
                for line in f:
                    if ": " in line:
                        word = line.split(": ", 1)[1].strip()
                        if self._is_valid_word_format(word):
                            added_words.add(word.upper())
        except (IOError, PermissionError) as e:
            logger.error(f"Could not read added words log: {e}")

        return added_words

    def _load_valid_words_from_file(self) -> set[str]:
        """
        Load base valid words from a file.
        Returns:
            Set of valid words
        Raises:
            FileNotFoundError: If the word list file doesn't exist
            ValueError: If no valid words are found in the file
            RuntimeError: If there's an error reading/parsing the file
        """
        valid_words = set()

        try:
            with open(self.base_valid_words_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip().upper()
                    if self._is_valid_word_format(word):
                        valid_words.add(word)

            if not valid_words:
                raise ValueError(f"No valid words found in {self.base_valid_words_path}")

            return valid_words

        except FileNotFoundError:
            raise FileNotFoundError(f"Word list file not found: {self.base_valid_words_path.absolute()}") from None
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Error loading word list from '{self.base_valid_words_path}': {e}") from e

    def _log_word(self, word: str) -> None:
        """Log a new word to the added words file."""
        try:
            # Ensure the directory exists
            self.added_valid_words_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.added_valid_words_path, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()}: {word}\n")
        except (IOError, PermissionError) as e:
            logger.error(f"Could not log added word to file: {e}")

    @staticmethod
    def _is_valid_word_format(word: str) -> bool:
        """
        Check if a word meets the basic format requirements.
        Note: Defensive programming - every word should be in valid format when this runs in this class.
        """
        return isinstance(word, str) and len(word) == WordList.WORD_LENGTH and word.isalpha()
