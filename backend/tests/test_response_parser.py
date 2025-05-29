import pytest

from wordle.response_parser import ResponseParser


class TestExtractQuotedWord:
    """Test suite for _extract_quoted_word method"""

    def test_double_quoted_word(self):
        """Test extracting word from double quotes"""
        response = 'My guess is "CRANE" for today.'
        result = ResponseParser._extract_quoted_word(response)
        assert result == "CRANE"

    def test_single_quoted_word(self):
        """Test extracting word from single quotes"""
        response = "My first guess is 'STARE'."
        result = ResponseParser._extract_quoted_word(response)
        assert result == "STARE"

    def test_multiple_quoted_words(self):
        """Test that it returns the first quoted 5-letter word"""
        response = 'Consider "HOUSE" or "CRANE" as options.'
        result = ResponseParser._extract_quoted_word(response)
        assert result == "HOUSE"

    def test_mixed_case_quoted_word(self):
        """Test extracting mixed case quoted word"""
        response = 'Let me try "World" this time.'
        result = ResponseParser._extract_quoted_word(response)
        assert result == "World"

    def test_quoted_non_five_letter_word(self):
        """Test when quoted word is not 5 letters"""
        response = 'I think it\'s "CAR" or "HOUSES".'
        with pytest.raises(ValueError, match="No quoted 5-letter word found"):
            ResponseParser._extract_quoted_word(response)

    def test_no_quoted_word(self):
        """Test when no quoted words exist"""
        response = "I think the answer is WORLD without quotes."
        with pytest.raises(ValueError, match="No quoted 5-letter word found"):
            ResponseParser._extract_quoted_word(response)

    def test_empty_quotes(self):
        """Test with empty quotes"""
        response = 'The word is "" apparently.'
        with pytest.raises(ValueError, match="No quoted 5-letter word found"):
            ResponseParser._extract_quoted_word(response)


class TestExtractCapitalizedWord:
    """Test suite for _extract_all_capitalized_word method"""

    def test_single_capitalized_word(self):
        """Test extracting a single all-caps word"""
        response = "I believe the answer is CRANE today."
        result = ResponseParser._extract_all_capitalized_word(response)
        assert result == "CRANE"

    def test_mixed_case_ignored(self):
        """Test that mixed case words are ignored"""
        response = "I think Crane or WORLD could work."
        result = ResponseParser._extract_all_capitalized_word(response)
        assert result == "WORLD"

    def test_capitalized_with_punctuation(self):
        """Test all-caps word with punctuation boundaries"""
        response = "The answer is WORLD! I'm sure."
        result = ResponseParser._extract_all_capitalized_word(response)
        assert result == "WORLD"

    def test_no_capitalized_word(self):
        """Test when no all-caps 5-letter word exists"""
        response = "I think it's crane or World in lowercase."
        with pytest.raises(ValueError, match="No capitalized 5-letter word found"):
            ResponseParser._extract_all_capitalized_word(response)

    def test_capitalized_wrong_length(self):
        """Test when all-caps words are not 5 letters"""
        response = "Maybe CAR or HOUSES in all caps."
        with pytest.raises(ValueError, match="No capitalized 5-letter word found"):
            ResponseParser._extract_all_capitalized_word(response)

class TestExtractLastWord:
    """Test suite for _extract_last_word method"""

    def test_last_word_five_letters(self):
        """Test when the last word is exactly 5 letters"""
        response = "My final guess is crane"
        result = ResponseParser._extract_last_word(response)
        assert result == "crane"

    def test_last_word_mixed_case(self):
        """Test last word with a mixed case"""
        response = "I'll go with World"
        result = ResponseParser._extract_last_word(response)
        assert result == "World"

    def test_last_word_with_punctuation(self):
        """Test last word followed by punctuation"""
        response = "The answer is WORLD."
        result = ResponseParser._extract_last_word(response)
        assert result == "WORLD"

    def test_single_word_response(self):
        """Test response with only one word"""
        response = "CRANE"
        result = ResponseParser._extract_last_word(response)
        assert result == "CRANE"

    def test_no_words(self):
        """Test response with no alphabetic words"""
        response = "123 456 789!"
        with pytest.raises(ValueError, match="Last word is not 5 letters"):
            ResponseParser._extract_last_word(response)


class TestResponseParserValidation:
    """Test suite for the validation method (validate_guess_format)"""

    def test_valid_five_letter_word(self):
        """Test validation of a valid 5-letter word"""
        assert ResponseParser.validate_guess_format("CRANE") is True
        assert ResponseParser.validate_guess_format("world") is True

    def test_invalid_length(self):
        """Test validation fails for the wrong length"""
        assert ResponseParser.validate_guess_format("CAR") is False
        assert ResponseParser.validate_guess_format("HOUSES") is False

    def test_invalid_characters(self):
        """Test validation fails for non-alphabetic characters"""
        assert ResponseParser.validate_guess_format("CR4NE") is False
        assert ResponseParser.validate_guess_format("12345") is False

    def test_empty_string(self):
        """Test validation fails for an empty string"""
        assert ResponseParser.validate_guess_format("") is False


class TestExtractGuessMultimethod:
    """Test suite for extract_guess_multimethod - the main extraction method"""

    def test_quoted_word(self):
        """Test quoted word - ignores other 5-letter words (think, guess)"""
        response = 'I think "crane" is a good guess'
        result = ResponseParser.extract_guess_multimethod(response)
        assert result == "CRANE"

    def test_all_capitalized_word(self):
        """Test all-caps word - ignores other 5-letter words (think, guess)"""
        response = "I think CRANE is a good guess"
        result = ResponseParser.extract_guess_multimethod(response)
        assert result == "CRANE"

    def test_last_word(self):
        """Test last word - ignores other 5-letter words (think, guess) and all caps (MY, IS)"""
        response = "MY final guess IS crane"
        result = ResponseParser.extract_guess_multimethod(response)
        assert result == "CRANE"
