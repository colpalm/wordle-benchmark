import re

class ResponseParser:
    """Parse LLM responses to extract Wordle guesses"""

    _PAT_QUOTED_WORD = re.compile(r'["\']([A-Za-z]{5})["\']')

    @staticmethod
    def extract_guess_multimethod(response: str) -> str:
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
            ResponseParser._extract_quoted_word,
            ResponseParser._extract_standalone_word,
            ResponseParser._extract_all_capitalized_word,
            ResponseParser._extract_last_word
        ]

        for method in extraction_methods:
            try:
                guess = method(response)
                if ResponseParser.validate_guess_format(guess):
                    return guess.upper()
            except (ValueError, AttributeError):
                continue

        # All methods failed
        raise ValueError(f"All extraction methods failed for response: '{response}'")

    @staticmethod
    def _extract_quoted_word(response: str) -> str:
        """Extract word from quotes"""
        matches = ResponseParser._PAT_QUOTED_WORD.findall(response)
        if matches:
            return matches[0]
        raise ValueError("No quoted 5-letter word found")

    @staticmethod
    def _extract_standalone_word(response: str) -> str:
        """Extract a standalone 5-letter word"""
        pattern = r'\b[A-Za-z]{5}\b'
        matches = re.findall(pattern, response)
        if matches:
            return matches[0]
        raise ValueError("No standalone 5-letter word found")

    @staticmethod
    def _extract_all_capitalized_word(response: str) -> str:
        """Extract all-caps word"""
        pattern = r'\b[A-Z]{5}\b'
        matches = re.findall(pattern, response)
        if matches:
            return matches[0]
        raise ValueError("No capitalized 5-letter word found")

    @staticmethod
    def _extract_last_word(response: str) -> str:
        pass


    @staticmethod
    def validate_guess_format(guess: str) -> bool:
        """
        Validate that a guess meets basic format requirements

        Args:
            guess: The extracted guess to validate

        Returns:
            True if the guess is a valid format, False otherwise
        """
        if not isinstance(guess, str):
            return False
        if len(guess) != 5:
            return False
        if not guess.isalpha():
            return False

        return True


