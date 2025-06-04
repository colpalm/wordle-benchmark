from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """
    Abstract base class for LLM clients that can play Wordle.

    This interface defines the contract that all LLM implementations must follow,
    allowing us to swap between different models (OpenAI, Anthropic, Grok, etc.)
    without changing the game logic.
    """

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """
        Generate a response from the LLM given a prompt.

        Args:
            prompt: The input prompt to send to the LLM

        Returns:
            The raw text response from the LLM

        Raises:
            LLMError: If the LLM request fails after retries
            LLMTimeoutError: If the request times out
            LLMRateLimitError: If rate limits are exceeded
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Return a human-readable identifier for this model.

        Returns:
                String identifier like "gpt-4o-mini", "claude-3-5-haiku", "llama3.1:8b"
        """
        pass

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """
        Return detailed information about the model for logging/analysis.

        Returns:
            Dictionary with model metadata like:
            {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "version": "2024-07-18",
                "max_tokens": 16384,
                "supports_system_messages": True
            }
        """
        pass