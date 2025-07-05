import textwrap
from abc import ABC, abstractmethod


class PromptTemplate(ABC):
    """Abstract base class for Wordle prompt templates"""

    # Base game instructions shared across all templates
    BASE_INSTRUCTIONS = textwrap.dedent("""
        You are playing Wordle. Guess the 5-letter word in 6 tries or fewer.

        Rules:
        - Each guess must be a valid 5-letter word
        - After each guess, you'll get feedback:
          * "correct" - letter is in the word and in the right position (green)
          * "present" - letter is in the word but in the wrong position (yellow)
          * "absent" - letter is not in the word (gray)
        """).lstrip()

    @abstractmethod
    def format_prompt(self, game_state: dict) -> str:
        """Format the current game state into a prompt for the LLM"""
        pass

    @abstractmethod
    def get_template_name(self) -> str:
        """Return the name/identifier for this template"""
        pass

    @staticmethod
    def _add_game_history(prompt: str, game_state: dict) -> str:
        """Add game history to prompt template - shared across all templates"""
        prompt_with_history = prompt + "\nPrevious Guesses:\n"

        for i, guess in enumerate(game_state["guesses"]):
            guess_result = game_state["guess_results"][i]
            prompt_with_history += f"{i + 1}. {guess}: "

            # Format result
            result_parts = []
            for letter_result in guess_result:
                letter = letter_result["letter"]
                status = letter_result["status"]
                result_parts.append(f"{letter} ({status})")

            prompt_with_history += ", ".join(result_parts) + "\n"

        prompt_with_history += "\n"
        return prompt_with_history

    @staticmethod
    def _add_current_state(prompt: str, game_state: dict) -> str:
        """Add the current game state to prompt template - shared across all templates"""
        guesses_made = game_state.get("guesses_made", 0)
        guesses_remaining = game_state.get("guesses_remaining", 6)
        prompt += f"Guesses made: {guesses_made}/6\n"
        prompt += f"Guesses remaining: {guesses_remaining}\n\n"

        return prompt

    @staticmethod
    def insert_feedback(prompt: str, feedback: str) -> str:
        """Insert feedback into prompt at a specific location - shared across all templates"""
        return prompt + feedback # Default: append


class SimplePromptTemplate(PromptTemplate):
    """Simple baseline prompt template with just the basic rules"""

    def get_template_name(self) -> str:
        return "simple"

    def format_prompt(self, game_state: dict) -> str:
        """Format a simple prompt with basic rules and game history"""
        # Base instructions
        prompt = self.BASE_INSTRUCTIONS

        # Add game history if available
        if game_state.get("guesses"):
            prompt = self._add_game_history(prompt, game_state)

        # Add current state
        prompt = self._add_current_state(prompt, game_state)

        # Request next guess
        prompt += "Respond with only your guess as a single 5-letter word.\n\n"
        prompt += "Your next guess:"

        return prompt


class JsonPromptTemplate(PromptTemplate):
    """JSON-based prompt template with chain-of-thought reasoning"""

    def get_template_name(self) -> str:
        return "json"

    def format_prompt(self, game_state: dict) -> str:
        """Format a prompt requesting JSON response with reasoning"""
        # Base instructions
        prompt = self.BASE_INSTRUCTIONS

        # Add game history if available
        if game_state.get("guesses"):
            prompt = self._add_game_history(prompt, game_state)

        # Add current state
        prompt = self._add_current_state(prompt, game_state)

        # Add JSON-specific instructions
        prompt += textwrap.dedent("""
        IMPORTANT: You must respond in valid JSON format with exactly two fields:
        {
            "reasoning": "Your 1-2 sentence explanation for your guess",
            "guess": "YOUR 5 LETTER WORD"
        }

        Example response:
        {
            "reasoning": "Based on the feedback, I know the word contains R in position 2 and E not in positions 3. I'll try a common word with R in position 2 and E in a different position.",
            "guess": "CRANE"
        }

        Your response:
        """).strip()

        return prompt

    def insert_feedback(self, prompt: str, feedback: str) -> str:
        """Insert feedback into the prompt at a specific location"""
        marker = "IMPORTANT: You must respond in valid JSON format"
        return prompt.replace(marker, feedback + marker)


class PromptTemplateFactory:
    """Factory class for creating prompt templates"""

    _templates = {
        "simple": SimplePromptTemplate,
        "json": JsonPromptTemplate,
    }

    @classmethod
    def create_template(cls, template_name: str) -> PromptTemplate:
        """Create a prompt template by name"""
        if template_name not in cls._templates:
            available = ", ".join(cls._templates.keys())
            raise ValueError(f"Unknown template '{template_name}'. Available: {available}")

        return cls._templates[template_name]()