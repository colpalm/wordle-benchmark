import pytest

from wordle.response_parser import JsonResponseParser, ResponseParserFactory, SimpleResponseParser


class TestExtractQuotedWord:
    """Test suite for _extract_quoted_word method"""

    def test_double_quoted_word(self):
        """Test extracting word from double quotes"""
        response = 'My guess is "CRANE" for today.'
        result = SimpleResponseParser._extract_quoted_word(response)
        assert result == "CRANE"

    def test_single_quoted_word(self):
        """Test extracting word from single quotes"""
        response = "My first guess is 'STARE'."
        result = SimpleResponseParser._extract_quoted_word(response)
        assert result == "STARE"

    def test_multiple_quoted_words(self):
        """Test that it returns the first quoted 5-letter word"""
        response = 'Consider "HOUSE" or "CRANE" as options.'
        result = SimpleResponseParser._extract_quoted_word(response)
        assert result == "HOUSE"

    def test_mixed_case_quoted_word(self):
        """Test extracting mixed case quoted word"""
        response = 'Let me try "World" this time.'
        result = SimpleResponseParser._extract_quoted_word(response)
        assert result == "World"

    def test_quoted_non_five_letter_word(self):
        """Test when quoted word is not 5 letters"""
        response = 'I think it\'s "CAR" or "HOUSES".'
        with pytest.raises(ValueError, match="No quoted 5-letter word found"):
            SimpleResponseParser._extract_quoted_word(response)

    def test_no_quoted_word(self):
        """Test when no quoted words exist"""
        response = "I think the answer is WORLD without quotes."
        with pytest.raises(ValueError, match="No quoted 5-letter word found"):
            SimpleResponseParser._extract_quoted_word(response)

    def test_empty_quotes(self):
        """Test with empty quotes"""
        response = 'The word is "" apparently.'
        with pytest.raises(ValueError, match="No quoted 5-letter word found"):
            SimpleResponseParser._extract_quoted_word(response)


class TestExtractCapitalizedWord:
    """Test suite for _extract_all_capitalized_word method"""

    def test_single_capitalized_word(self):
        """Test extracting a single all-caps word"""
        response = "I believe the answer is CRANE today."
        result = SimpleResponseParser._extract_all_capitalized_word(response)
        assert result == "CRANE"

    def test_mixed_case_ignored(self):
        """Test that mixed case words are ignored"""
        response = "I think Crane or WORLD could work."
        result = SimpleResponseParser._extract_all_capitalized_word(response)
        assert result == "WORLD"

    def test_capitalized_with_punctuation(self):
        """Test all-caps word with punctuation boundaries"""
        response = "The answer is WORLD! I'm sure."
        result = SimpleResponseParser._extract_all_capitalized_word(response)
        assert result == "WORLD"

    def test_no_capitalized_word(self):
        """Test when no all-caps 5-letter word exists"""
        response = "I think it's crane or World in lowercase."
        with pytest.raises(ValueError, match="No capitalized 5-letter word found"):
            SimpleResponseParser._extract_all_capitalized_word(response)

    def test_capitalized_wrong_length(self):
        """Test when all-caps words are not 5 letters"""
        response = "Maybe CAR or HOUSES in all caps."
        with pytest.raises(ValueError, match="No capitalized 5-letter word found"):
            SimpleResponseParser._extract_all_capitalized_word(response)

class TestExtractLastWord:
    """Test suite for _extract_last_word method"""

    def test_last_word_five_letters(self):
        """Test when the last word is exactly 5 letters"""
        response = "My final guess is crane"
        result = SimpleResponseParser._extract_last_word(response)
        assert result == "crane"

    def test_last_word_mixed_case(self):
        """Test last word with a mixed case"""
        response = "I'll go with World"
        result = SimpleResponseParser._extract_last_word(response)
        assert result == "World"

    def test_last_word_with_punctuation(self):
        """Test last word followed by punctuation"""
        response = "The answer is WORLD."
        result = SimpleResponseParser._extract_last_word(response)
        assert result == "WORLD"

    def test_single_word_response(self):
        """Test response with only one word"""
        response = "CRANE"
        result = SimpleResponseParser._extract_last_word(response)
        assert result == "CRANE"

    def test_no_words(self):
        """Test response with no alphabetic words"""
        response = "123 456 789!"
        with pytest.raises(ValueError, match="Last word is not 5 letters"):
            SimpleResponseParser._extract_last_word(response)


class TestSimpleResponseParser:
    """Test suite for SimpleResponseParser - the main extraction method"""

    @pytest.fixture
    def parser(self):
        """Returns a SimpleResponseParser instance for tests"""
        return SimpleResponseParser()

    def test_quoted_word(self, parser):
        """Test quoted word - ignores other 5-letter words (think, guess)"""
        response = 'I think "crane" is a good guess'
        result = parser.extract_guess(response)
        assert result == "CRANE"

    def test_all_capitalized_word(self, parser):
        """Test all-caps word - ignores other 5-letter words (think, guess)"""
        response = "I think CRANE is a good guess"
        result = parser.extract_guess(response)
        assert result == "CRANE"

    def test_last_word(self, parser):
        """Test last word - ignores other 5-letter words (think, guess) and all caps (MY, IS)"""
        response = "MY final guess IS crane"
        result = parser.extract_guess(response)
        assert result == "CRANE"

    def test_get_parser_name(self, parser):
        """Test get_parser_name returns the correct identifier"""
        assert parser.get_parser_name() == "simple"


class TestJsonResponseParser:
    """Test suite for JsonResponseParser"""

    @pytest.fixture
    def parser(self):
        """Returns a JSONResponseParser instance for tests"""
        return JsonResponseParser()

    def test_valid_json_response(self, parser):
        """Test parsing a valid JSON response with the guess field"""
        response = '{"reasoning": "This is my reasoning", "guess": "CRANE"}'
        result = parser.extract_guess(response)
        reasoning_response = parser.extract_reasoning(response)
        assert result == "CRANE"
        assert reasoning_response == "This is my reasoning"

    def test_valid_json_lowercase_guess(self, parser):
        """Test parsing a valid JSON response with lowercase guess"""
        response = '{"reasoning": "This is my reasoning", "guess": "crane"}'
        result = parser.extract_guess(response)
        assert result == "CRANE"

    def test_valid_json_mixed_case_guess(self, parser):
        """Test parsing a valid JSON response with mixed case guess"""
        response = '{"reasoning": "This is my reasoning", "guess": "Crane"}'
        result = parser.extract_guess(response)
        assert result == "CRANE"

    def test_json_missing_guess_field(self, parser):
        """Test JSON response missing the guess field"""
        response = '{"reasoning": "This is my reasoning"}'
        with pytest.raises(ValueError, match="JSON response missing 'guess' field"):
            parser.extract_guess(response)

    def test_json_missing_reasoning_field(self, parser):
        """Test JSON response missing the reasoning field"""
        response = '{"guess": "CRANE"}'
        with pytest.raises(ValueError, match="JSON response missing 'reasoning' field"):
            parser.extract_reasoning(response)

    def test_invalid_json_format(self, parser):
        """Test invalid JSON format"""
        response = 'This is not JSON'
        with pytest.raises(ValueError, match="Failed to parse JSON response"):
            parser.extract_guess(response)

    def test_invalid_guess_format(self, parser):
        """Test JSON with an invalid guess format (not 5 letters)"""
        response = '{"reasoning": "This is my reasoning", "guess": "CAR"}'
        with pytest.raises(ValueError, match="Invalid guess format"):
            parser.extract_guess(response)

    def test_get_parser_name(self, parser):
        """Test get_parser_name returns the correct identifier"""
        assert parser.get_parser_name() == "json"


class TestResponseParserFactory:
    """Test suite for ResponseParserFactory"""

    @pytest.mark.parametrize("parser_name, expected_class", [
        ("simple", SimpleResponseParser),
        ("json", JsonResponseParser),
    ])
    def test_create_parser(self, parser_name, expected_class):
        """Test creating parsers by name"""
        parser = ResponseParserFactory.create_parser(parser_name)
        assert isinstance(parser, expected_class)
        assert parser.get_parser_name() == parser_name

    def test_unknown_parser(self):
        """Test error when requesting an unknown parser"""
        with pytest.raises(ValueError, match="Unknown parser 'unknown'"):
            ResponseParserFactory.create_parser("unknown")
