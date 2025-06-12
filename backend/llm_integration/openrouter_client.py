from llm_integration.llm_client import LLMClient


class OpenRouterClient(LLMClient):
    """
    OpenRouter client implementation.
    Using OpenRouter since it provides a one-stop shop for all LLM models. Will implement specific model
    clients if needed.
    """

    def __init__(self, api_key: str, model: str):
        """
        Initialize OpenRouter client with API key and model name.

        Args:
            api_key: OpenRouter API key
            model: Model name (e.g., "gpt-4o-mini", "gpt-4", "x-ai/grok-3-beta", "anthropic/claude-opus-4")
        """
        self.api_key = api_key
        self.model = model

    def generate_response(self, prompt: str) -> str:
        """
        Generate a response from OpenRouter API
        """
        # TODO: Implement actual API call
        raise NotImplementedError("generate_response not yet implemented")

    def get_model_name(self) -> str:
        """
        Return the configured model name
        """
        return self.model