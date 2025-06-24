import os
import pytest
from dotenv import load_dotenv

from llm_integration.openrouter_client import OpenRouterClient
from llm_integration.llm_client import LLMError

load_dotenv()


@pytest.mark.integration
@pytest.mark.api_calls
class TestLLMClientIntegration:
    """Integration tests for LLM clients - makes real API calls"""

    def test_openrouter_client_generates_response(self):
        """
        GIVEN I have an OpenRouter client with valid credentials
        WHEN I send a simple prompt to the LLM API
        THEN I should get a coherent response back
        """
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            pytest.skip("OPENROUTER_API_KEY not set in environment")

        # Use an inexpensive model for testing
        client = OpenRouterClient(api_key=api_key, model="gpt-3.5-turbo")

        try:
            response = client.generate_response("Say exactly: HELLO")

            # Basic assertions
            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
            assert "HELLO" in response.upper()

            print(f"\n✓ Successful API call. Response: '{response}'")

        except LLMError as e:
            pytest.fail(f"LLM API call failed: {e}")

    def test_openrouter_client_handles_wordle_prompt(self):
        """
        GIVEN I have an OpenRouter client
        WHEN I send a Wordle-like prompt
        THEN I should get a 5-letter word response
        """
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            pytest.skip("OPENROUTER_API_KEY not set in environment")

        client = OpenRouterClient(api_key=api_key, model="gpt-3.5-turbo")

        prompt = """You are playing Wordle. Guess a 5-letter word.

        Respond with only your guess as a single 5-letter word.

        Your guess:"""

        try:
            response = client.generate_response(prompt)

            # Extract potential word from the response (might have extra text)
            words = [word for word in response.split() if len(word) == 5 and word.isalpha()]

            assert len(words) >= 1, f"No 5-letter word found in response: '{response}'"

            # At least one 5-letter word should be present
            guess = words[0].upper()
            assert len(guess) == 5
            assert guess.isalpha()

            print(f"\n✓ Successful Wordle-style response. Guess: '{guess}'")
            print(f"  Full response: '{response}'")

        except LLMError as e:
            pytest.fail(f"LLM API call failed: {e}")

    def test_invalid_api_key_raises_authentication_error(self):
        """
        GIVEN I have an OpenRouter client with invalid credentials
        WHEN I try to make an API call
        THEN I should get an authentication error
        """
        client = OpenRouterClient(api_key="invalid-key", model="gpt-3.5-turbo")

        from llm_integration.llm_client import LLMAuthenticationError

        with pytest.raises(LLMAuthenticationError, match="Invalid API key"):
            client.generate_response("test")

    def test_model_name_getter(self):
        """Test that get_model_name works correctly"""
        client = OpenRouterClient(api_key="fake-key", model="test-model")
        assert client.get_model_name() == "test-model"