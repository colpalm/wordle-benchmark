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
    def get_current_usage_stats(self) -> dict[str, Any]:
        """
        Get usage statistics from the most recent API call.

        Returns:
            Dictionary containing usage statistics like token counts, cost, response time
        """
        pass


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM requests timeout."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limits are exceeded."""

    pass


class LLMAuthenticationError(LLMError):
    """Raised when LLM authentication fails (an invalid API key, etc.)."""

    pass


class LLMQuotaExceededError(LLMError):
    """Raised when LLM quota/credits are exhausted."""

    pass
