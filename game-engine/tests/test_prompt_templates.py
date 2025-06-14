import pytest

from wordle.prompt_templates import PromptTemplateFactory, SimplePromptTemplate


class TestPromptTemplateFactory:
    """Test the PromptTemplateFactory class."""

    def test_create_simple_template(self):
        """Test creating a simple template"""
        template = PromptTemplateFactory.create_template("simple")
        assert isinstance(template, SimplePromptTemplate)
        assert template.get_template_name() == "simple"

    def test_create_invalid_template(self):
        """Test error handling for invalid template names"""
        with pytest.raises(ValueError, match="Unknown template 'invalid'"):
            PromptTemplateFactory.create_template("invalid")

class TestSimplePromptTemplate:
    """Test suite for SimplePromptTemplate"""

    @pytest.fixture
    def simple_template(self):
        """Fixture providing a SimplePromptTemplate instance"""
        return SimplePromptTemplate()

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

    def test_template_name(self, simple_template):
        """Test that template returns the correct name"""
        assert simple_template.get_template_name() == "simple"

    def test_prompt_is_string(self, simple_template, empty_game_state):
        """Test that prompt returns a string"""
        prompt = simple_template.format_prompt(empty_game_state)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_first_guess_prompt_structure(self, simple_template, empty_game_state):
        """Test the structure of the first guess prompt"""
        prompt = simple_template.format_prompt(empty_game_state)

        # Check that basic elements are present
        assert "You are playing Wordle" in prompt
        assert "Guess the 5-letter word in 6 tries" in prompt
        assert "Rules:" in prompt
        assert "correct" in prompt and "green" in prompt
        assert "present" in prompt and "yellow" in prompt
        assert "absent" in prompt and "gray" in prompt
        assert "Guesses made: 0/6" in prompt
        assert "Guesses remaining: 6" in prompt
        assert "Your next guess:" in prompt

        # Should NOT contain the previous guesses section for empty state
        assert "Previous guesses:" not in prompt

        print(f"\n{"=" * 10} PROMPT TEMPLATE WITH NO GUESSES {"=" * 10}")
        print(prompt)  # Can view template when running tests with -s

    def test_prompt_with_game_history(self, simple_template, game_with_one_guess):
        """Test prompt includes game history correctly"""
        prompt = simple_template.format_prompt(game_with_one_guess)

        # Should include previous guesses
        assert "Previous Guesses:" in prompt
        assert "1. STARE:" in prompt
        assert "S(absent)" in prompt
        assert "A(correct)" in prompt
        assert "R(present)" in prompt
        assert "Guesses made: 1/6" in prompt
        assert "Guesses remaining: 5" in prompt

        print(f"\n{"=" * 10} PROMPT TEMPLATE WITH ONE GUESS {"=" * 10}")
        print(prompt)  # Can view template when running tests with -s

    def test_prompt_with_multiple_guesses(self, simple_template, game_with_multiple_guesses):
        """Test prompt with multiple guesses in history"""
        prompt = simple_template.format_prompt(game_with_multiple_guesses)

        # Check both guesses are included
        assert "1. STARE:" in prompt
        assert "2. CLOUD:" in prompt
        assert "C(present)" in prompt
        assert "L(absent)" in prompt
        assert "Guesses made: 2/6" in prompt
        assert "Guesses remaining: 4" in prompt

        print(f"\n{"=" * 10} PROMPT TEMPLATE WITH MULTIPLE GUESSES {"=" * 10}")
        print(prompt) # Can view template when running tests with -s

    def test_guess_result_formatting(self, simple_template, game_with_one_guess):
        """Test that guess results are formatted correctly"""
        prompt = simple_template.format_prompt(game_with_one_guess)

        # Check the specific format: LETTER(status)
        assert "S(absent)" in prompt
        assert "T(absent)" in prompt
        assert "A(correct)" in prompt
        assert "R(present)" in prompt
        assert "E(correct)" in prompt

    def test_prompt_ends_correctly(self, simple_template, empty_game_state):
        """Test that prompt ends with request for guess"""
        prompt = simple_template.format_prompt(empty_game_state)
        assert prompt.endswith("Your next guess:")

    def test_response_format_instruction(self, simple_template, empty_game_state):
        """Test that prompt includes response format instruction"""
        prompt = simple_template.format_prompt(empty_game_state)
        assert "Respond with only your guess as a single 5-letter word" in prompt