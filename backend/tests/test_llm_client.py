from llm_integration.openai_client import OpenAIClient


class TestOpenAIClient:
    """Unit tests for OpenAI client that don't require external API calls"""

    def test_get_model_name(self):
        """Return the model name"""
        client = OpenAIClient(api_key="fake-key", model="gpt-4o-mini")
        model_name = client.get_model_name()
        assert model_name == "gpt-4o-mini"
