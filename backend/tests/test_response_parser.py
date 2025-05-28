from wordle.response_parser import ResponseParser


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