from typing import Any

from llm_integration.llm_client import LLMClient


class OpenAIClient(LLMClient):
    """OpenAI API client implementation"""

    def __init__(self, api_key: str, model: str):
        """
        Initialize OpenAI client

        Args:
            api_key: OpenAI API key
            model: Model name (e.g., "gpt-4o-mini", "gpt-4")
        """
        self.api_key = api_key
        self.model = model

    def generate_response(self, prompt: str) -> str:
        """
        Generate a response from OpenAI API
        """
        # TODO: Implement actual API call
        raise NotImplementedError("generate_response not yet implemented")

    def get_model_name(self) -> str:
        """
        Return the configured model name
        """
        return self.model