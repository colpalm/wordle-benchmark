from llm_integration.openrouter_client import OpenRouterClient


class TestOpenRouterClient:
    """Unit tests for OpenRouter client that don't require external API calls"""

    def test_get_model_name(self):
        """Return the model name"""
        client = OpenRouterClient(api_key="fake-key", model="gpt-4o-mini")
        model_name = client.get_model_name()
        assert model_name == "gpt-4o-mini"
