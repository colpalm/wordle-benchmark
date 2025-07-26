import pytest

from utils.logging_config import get_logger
from wordle.prompt_templates import JsonPromptTemplate, PromptTemplateFactory, SimplePromptTemplate

logger = get_logger(__name__)

class BasePromptTemplate:
    """Base test class with common tests for all prompt templates"""

    @pytest.fixture
    def template(self):
        """Subclasses must override this to provide their template instance"""
        raise NotImplementedError("Subclasses must provide a template fixture")

    @pytest.fixture
    def empty_game_state(self):
        """Fixture for a fresh game state (no guesses made)"""
        return {
            "guesses": [],
            "guess_results": [],
            "guesses_made": 0,
            "guesses_remaining": 6
        }

    @pytest.fixture
    def game_with_one_guess(self):
        """Fixture for game state with one guess made"""
        return {
            "guesses": ["STARE"],
            "guess_results": [
                [
                    {"letter": "S", "status": "absent"},
                    {"letter": "T", "status": "absent"},
                    {"letter": "A", "status": "correct"},
                    {"letter": "R", "status": "present"},
                    {"letter": "E", "status": "correct"}
                ]
            ],
            "guesses_made": 1,
            "guesses_remaining": 5
        }

    @pytest.fixture
    def game_with_multiple_guesses(self):
        """Fixture for game state with multiple guesses"""
        return {
            "guesses": ["STARE", "CLOUD"],
            "guess_results": [
                [
                    {"letter": "S", "status": "absent"},
                    {"letter": "T", "status": "absent"},
                    {"letter": "A", "status": "correct"},
                    {"letter": "R", "status": "present"},
                    {"letter": "E", "status": "correct"}
                ],
                [
                    {"letter": "C", "status": "present"},
                    {"letter": "L", "status": "absent"},
                    {"letter": "O", "status": "absent"},
                    {"letter": "U", "status": "absent"},
                    {"letter": "D", "status": "absent"}
                ]
            ],
            "guesses_made": 2,
            "guesses_remaining": 4
        }

    @staticmethod
    def determine_prompt_logging_header(template) -> str:
        """Based on the prompt template, configure the header statement"""
        if isinstance(template, SimplePromptTemplate):
            return f"\n{"=" * 10} SIMPLE PROMPT TEMPLATE WITH NO GUESSES {"=" * 10}"
        else:
            return f"\n{'=' * 10} JSON PROMPT TEMPLATE WITH NO GUESSES {'=' * 10}"

    # ===== ABSTRACT METHODS FOR SUBCLASSES =====

    def get_expected_template_name(self):
        """Subclasses must override this to provide the expected template name"""
        raise NotImplementedError("Subclasses must provide expected template name")

    # ===== COMMON TESTS FOR ALL TEMPLATES =====

    def test_template_name(self, template):
        """Test that template returns the correct name"""
        expected_name = self.get_expected_template_name()
        assert template.get_template_name() == expected_name

    @staticmethod
    def test_prompt_is_string(template, empty_game_state):
        """Test that prompt returns a string"""
        prompt = template.format_prompt(empty_game_state)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_first_guess_prompt_structure(self, template, empty_game_state):
        """Test the base structure common to all templates"""
        prompt = template.format_prompt(empty_game_state)

        # Check that basic elements are present
        assert "You are playing Wordle" in prompt
        assert "Guess the 5-letter word in 6 tries" in prompt
        assert "Rules:" in prompt
        assert "correct" in prompt and "green" in prompt
        assert "present" in prompt and "yellow" in prompt
        assert "absent" in prompt and "gray" in prompt
        assert "Guesses made: 0/6" in prompt
        assert "Guesses remaining: 6" in prompt

        # Should NOT contain the previous guesses section for empty state
        assert "Previous guesses:" not in prompt

        # Can view template when running tests with -s
        prompt_header = self.determine_prompt_logging_header(template)
        logger.debug(prompt_header)
        logger.debug(prompt)

    def test_prompt_with_game_history(self, template, game_with_one_guess):
        """Test prompt includes game history correctly"""
        prompt = template.format_prompt(game_with_one_guess)

        # Should include previous guesses
        assert "Previous Guesses:" in prompt
        assert "1. STARE:" in prompt
        assert "S (absent)" in prompt
        assert "A (correct)" in prompt
        assert "R (present)" in prompt
        assert "Guesses made: 1/6" in prompt
        assert "Guesses remaining: 5" in prompt

        # Can view template when running tests with -s
        prompt_header = self.determine_prompt_logging_header(template)
        logger.debug(prompt_header)
        logger.debug(prompt)

    def test_prompt_with_multiple_guesses(self, template, game_with_multiple_guesses):
        """Test prompt with multiple guesses in history"""
        prompt = template.format_prompt(game_with_multiple_guesses)

        # Check both guesses are included
        assert "1. STARE:" in prompt
        assert "2. CLOUD:" in prompt
        assert "C (present)" in prompt
        assert "L (absent)" in prompt
        assert "Guesses made: 2/6" in prompt
        assert "Guesses remaining: 4" in prompt

        # Can view template when running tests with -s
        prompt_header = self.determine_prompt_logging_header(template)
        logger.debug(prompt_header)
        logger.debug(prompt)

    @staticmethod
    def test_guess_result_formatting(template, game_with_one_guess):
        """Test that guess results are formatted correctly"""
        prompt = template.format_prompt(game_with_one_guess)

        # Check the specific format: LETTER(status)
        assert "S (absent)" in prompt
        assert "T (absent)" in prompt
        assert "A (correct)" in prompt
        assert "R (present)" in prompt
        assert "E (correct)" in prompt


class TestPromptTemplateFactory:
    """Test the PromptTemplateFactory class."""

    def test_create_simple_template(self):
        """Test creating a simple template"""
        template = PromptTemplateFactory.create_template("simple")
        assert isinstance(template, SimplePromptTemplate)
        assert template.get_template_name() == "simple"

    def test_create_json_template(self):
        """Test creating a JSON template"""
        template = PromptTemplateFactory.create_template("json")
        assert isinstance(template, JsonPromptTemplate)
        assert template.get_template_name() == "json"

    def test_create_invalid_template(self):
        """Test error handling for invalid template names"""
        with pytest.raises(ValueError, match="Unknown template 'invalid'"):
            PromptTemplateFactory.create_template("invalid")

class TestSimplePromptTemplate(BasePromptTemplate):
    """Test suite for SimplePromptTemplate"""

    @pytest.fixture
    def template(self):
        """Fixture providing a SimplePromptTemplate instance"""
        return SimplePromptTemplate()

    def get_expected_template_name(self):
        """Return the expected template name for SimplePromptTemplate"""
        return "simple"

    # ===== SIMPLE TEMPLATE SPECIFIC TESTS =====

    def test_prompt_ends_correctly(self, template, empty_game_state):
        """Test that prompt ends with a request for guess"""
        prompt = template.format_prompt(empty_game_state)
        assert prompt.endswith("Your next guess:")

    def test_response_format_instruction(self, template, empty_game_state):
        """Test that prompt includes response format instruction"""
        prompt = template.format_prompt(empty_game_state)
        assert "Respond with only your guess as a single 5-letter word" in prompt

class TestJsonPromptTemplate(BasePromptTemplate):
    """Test suite for JsonPromptTemplate"""

    @pytest.fixture
    def template(self):
        """Fixture providing a JsonPromptTemplate instance"""
        return JsonPromptTemplate()

    def get_expected_template_name(self):
        """Return the expected template name for JsonPromptTemplate"""
        return "json"

    # ===== JSON TEMPLATE SPECIFIC TESTS =====

    def test_json_format_instructions(self, template, empty_game_state):
        """Test that prompt includes JSON format instructions"""
        prompt = template.format_prompt(empty_game_state)

        # Check for JSON format instructions
        assert "IMPORTANT: You must respond in valid JSON format with exactly two fields" in prompt
        assert "reasoning" in prompt
        assert "guess" in prompt

    def test_reasoning_limit_instruction(self, template, empty_game_state):
        """Test that the prompt specifies the 1-2 sentence limit for reasoning"""
        prompt = template.format_prompt(empty_game_state)
        assert "1-2 sentence" in prompt and "reasoning" in prompt

    def test_json_example_included(self, template, empty_game_state):
        """Test that prompt includes an example of the expected JSON format"""
        prompt = template.format_prompt(empty_game_state)

        # Check for JSON example
        assert "{" in prompt and "}" in prompt
        assert '"reasoning":' in prompt
        assert '"guess":' in prompt
