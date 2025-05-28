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

class TestExtractStandaloneWord:
    """Test suite for _extract_standalone_word method"""

    def test_single_standalone_word(self):
        """Test extracting a single standalone 5-letter word"""
        response = "CRANE"
        result = ResponseParser._extract_standalone_word(response)
        assert result == "CRANE"

    def test_standalone_word_in_sentence(self):
        """Test extracting a single standalone 5-letter word"""
        response = "The word is CRANE today."
        result = ResponseParser._extract_standalone_word(response)
        assert result == "CRANE"

    def test_multiple_standalone_words(self):
        """Test that it returns the first standalone 5-letter word"""
        response = "STARE and HOUSE are good guesses."
        result = ResponseParser._extract_standalone_word(response)
        assert result == "STARE"


class TestExtractGuessMultimethod:
    """Test suite for extract_guess_multimethod - the main extraction method"""

    def test_quoted_word(self):
        """Test quoted word method"""
        response = 'I think "CRANE" is a good guess'
        result = ResponseParser.extract_guess_multimethod(response)
        assert result == "CRANE" # bypasses 5 letter 'think' and gets 'CRANE'