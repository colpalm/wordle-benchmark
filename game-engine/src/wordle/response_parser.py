import json
import re
from abc import ABC, abstractmethod
from typing import Optional

from wordle.wordle_game import WordleGame


class ResponseParser(ABC):
    """Abstract base class for parsing LLM responses to extract Wordle guesses"""

    @abstractmethod
    def extract_guess(self, response: str) -> str:
        """
        Extract a guess from the LLM response

        Args:
            response: Raw text response from LLM

        Returns:
            Extracted guess

        Raises:
            ValueError: If extraction fails
        """
        pass

    @abstractmethod
    def get_parser_name(self) -> str:
        """Return the name/identifier for this parser"""
        pass

    def extract_reasoning(self, response: str) -> Optional[str]:
        """
        Extract reasoning from the LLM response if available

        Args:
            response: Raw text response from LLM

        Returns:
            Extracted reasoning text, or None if not available/applicable
        """
        # Default implementation - parsers can override if they support reasoning
        return None


class SimpleResponseParser(ResponseParser):
    """Parser for simple text responses with quoted words, all-caps, or last word extraction"""

    _PAT_QUOTED_WORD = re.compile(r'["\']([A-Za-z]{5})["\']')
    _PAT_ALL_CAPS = re.compile(r"\b[A-Z]{5}\b")
    _PAT_5_LETTER_WORDS = re.compile(r"\b[A-Za-z]{5}\b")

    def get_parser_name(self) -> str:
        return "simple"

    def extract_guess(self, response: str) -> str:
        """
        Try multiple extraction methods in order of preference

        Args:
            response: Raw text response from LLM

        Returns:
            Best extracted guess

        Raises:
            ValueError: If all methods fail
        """
        response = response.strip()
        extraction_methods = [
            SimpleResponseParser._extract_quoted_word,
            SimpleResponseParser._extract_all_capitalized_word,
            SimpleResponseParser._extract_last_word,
        ]

        for method in extraction_methods:
            try:
                guess = method(response)
                is_valid, _ = WordleGame.validate_guess_format(guess)
                if is_valid:
                    return guess.upper()
            except (ValueError, AttributeError):
                continue

        # All methods failed
        raise ValueError(f"All extraction methods failed for response: '{response}'")

    @staticmethod
    def _extract_quoted_word(response: str) -> str:
        """Extract word from quotes"""
        matches = SimpleResponseParser._PAT_QUOTED_WORD.findall(response)
        if matches:
            return matches[0]
        raise ValueError("No quoted 5-letter word found")

    @staticmethod
    def _extract_all_capitalized_word(response: str) -> str:
        """Extract all-caps word"""
        matches = re.findall(SimpleResponseParser._PAT_ALL_CAPS, response)
        if matches:
            return matches[0]
        raise ValueError("No capitalized 5-letter word found")

    @staticmethod
    def _extract_last_word(response: str) -> str:
        """Extract the last word if it's 5 letters"""
        words = re.findall(SimpleResponseParser._PAT_5_LETTER_WORDS, response)
        if words:
            return words[-1]
        raise ValueError("Last word is not 5 letters")


class JsonResponseParser(ResponseParser):
    """Parser for JSON-formatted responses with reasoning and guess fields"""

    def get_parser_name(self) -> str:
        return "json"

    def extract_guess(self, response: str) -> str:
        """
        Extract a guess from a JSON-formatted response

        Args:
            response: JSON-formatted response from LLM

        Returns:
            Extracted guess

        Raises:
            ValueError: If JSON parsing fails or required fields are missing
        """
        json_data = self._parse_json_response(response)

        # Extract guess field
        try:
            guess = json_data["guess"]
        except KeyError:
            raise ValueError("JSON response missing 'guess' field") from None

        # Validate guess format
        is_valid, error_msg = WordleGame.validate_guess_format(guess)
        if not is_valid:
            raise ValueError(f"Invalid guess format: {error_msg}")

        return guess.upper()

    def extract_reasoning(self, response: str) -> Optional[str]:
        """
        Extract reasoning from a JSON-formatted response

        Args:
            response: JSON-formatted response from LLM

        Returns:
            Extracted reasoning text, or None if not present

        Raises:
            ValueError: If JSON parsing fails or the reasoning field is missing
        """
        json_data = self._parse_json_response(response)
        try:
            return json_data["reasoning"]
        except KeyError:
            raise ValueError("JSON response missing 'reasoning' field") from None

    @staticmethod
    def _parse_json_response(response: str) -> dict:
        """
        Parse JSON response with helpful error messages

        Args:
            response: Raw response string

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            response = response.strip()
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}") from e


class ResponseParserFactory:
    """Factory class for creating response parsers"""

    _parsers = {
        "simple": SimpleResponseParser,
        "json": JsonResponseParser,
    }

    @classmethod
    def create_parser(cls, parser_name: str) -> ResponseParser:
        """Create a response parser by name"""
        if parser_name not in cls._parsers:
            available = ", ".join(cls._parsers.keys())
            raise ValueError(f"Unknown parser '{parser_name}'. Available: {available}")

        return cls._parsers[parser_name]()
