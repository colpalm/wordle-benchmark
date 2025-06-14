import os
import pytest
from dotenv import load_dotenv

from llm_integration.openrouter_client import OpenRouterClient

load_dotenv()


@pytest.mark.integration
class TestLLMClientIntegration:
    """Integration tests for LLM clients"""

    @pytest.mark.api_calls
    def test_client_can_generate_a_response(self):
        """
        GIVEN I have an <llm client> with valid credentials
        WHEN I send a simple prompt to the LLM API
        THEN I should get a response back
        """
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            pytest.skip("OPENROUTER_API_KEY not set")

        # Inexpensive model for testing
        open_ai_testing_model = "gpt-3.5-turbo"
        client = OpenRouterClient(api_key, open_ai_testing_model)
        response = client.generate_response("What is the meaning of life?")
        assert response is not None
        assert len(response) > 0
