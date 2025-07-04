import json
import time
from typing import Optional

import requests

from llm_integration.llm_client import (
    LLMClient,
    LLMError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMQuotaExceededError
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


class OpenRouterClient(LLMClient):
    """
    OpenRouter client implementation.
    Using OpenRouter since it provides a one-stop shop for all LLM models. Will implement specific model
    clients if needed.
    """

    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # For general errors (network issues, etc.)
    RATE_LIMIT_DELAY = 15.0  # For rate limits specifically

    def __init__(self, api_key: str, model: str, timeout: Optional[int] = None):
        """
        Initialize OpenRouter client with API key and model name.

        Args:
            api_key: OpenRouter API key
            model: Model name (e.g., "gpt-4o-mini", "gpt-4", "x-ai/grok-3-beta", "anthropic/claude-3-5-sonnet")
            timeout: Request timeout in seconds (defaults to 30)
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout or self.DEFAULT_TIMEOUT

    def generate_response(self, prompt: str) -> str:
        """
        Generate a response from OpenRouter API with retries and error handling

        Args:
            prompt: The input prompt to send to the LLM

        Returns:
            The raw text response from the LLM

        Raises:
            LLMAuthenticationError: If API key is invalid
            LLMQuotaExceededError: If quota/credits are exhausted
            LLMRateLimitError: If rate limits are exceeded
            LLMTimeoutError: If the request times out
            LLMError: For other API errors
        """
        payload = self._build_request_payload(prompt)

        for attempt in range(self.MAX_RETRIES):
            logger.debug(f"Making API request to {self.model} (attempt {attempt + 1}/{self.MAX_RETRIES})")

            try:
                response = self._make_api_request(payload)

                # Handle HTTP status codes - may sleep and continue to next attempt
                if self._handle_http_status_codes(response, attempt):
                    continue  # Rate limit handled, try again

                # Successfully got a good response
                content = self._extract_content_from_response(response)
                logger.debug(f"Successfully received response from {self.model}")
                return content.strip()

            except (LLMAuthenticationError, LLMQuotaExceededError):
                # Don't retry these errors
                raise
            except LLMTimeoutError as e:
                if not self._should_retry_attempt(attempt):
                    raise e
                self._handle_retry_delay(e, attempt)

        # Raise an error if all retries failed
        raise LLMError("All retry attempts failed")

    def _build_request_payload(self, prompt: str) -> dict:
        """Build the API request payload"""
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 200,  # Sufficient for JSON with brief reasoning
        }

    def _make_api_request(self, payload: dict) -> requests.Response:
        """Make the actual HTTP request to the API"""
        url = f"{self.BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/colpalm/wordle-benchmark",  # Optional: for analytics
            "X-Title": "Wordle Benchmark"  # Optional: for analytics
        }

        try:
            return requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
        except requests.exceptions.Timeout as e:
            raise LLMTimeoutError(f"Request timed out after {self.timeout}s: {e}")
        except requests.exceptions.ConnectionError as e:
            raise LLMError(f"Connection failed: {e}")

    def _handle_http_status_codes(self, response: requests.Response, attempt: int) -> bool:
        """
        Handle specific HTTP status codes with appropriate retries

        Returns:
            True if the caller should continue to next retry attempt
            False if processing should continue normally
        """
        if response.status_code == 401:
            raise LLMAuthenticationError("Invalid API key")

        if response.status_code == 402:
            raise LLMQuotaExceededError("Quota or credits exhausted")

        if response.status_code == 429:
            self._handle_rate_limit(attempt)
            return True  # Signal caller to continue retry loop

        # Raise for other HTTP errors
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise LLMError(f"HTTP error {response.status_code}: {e}")

        return False

    def _handle_rate_limit(self, attempt: int) -> None:
        """Handle rate limiting with exponential backoff"""
        if attempt >= self.MAX_RETRIES - 1:
            raise LLMRateLimitError("Rate limit exceeded after retries")

        wait_time = self.RATE_LIMIT_DELAY * (2 ** attempt)  # 15s, 30s, 60s
        logger.warning(f"Rate limited, waiting {wait_time}s before retry...")
        time.sleep(wait_time)

    @staticmethod
    def _extract_content_from_response(response: requests.Response) -> str:
        """Extract and validate content from API response"""
        # Parse the response JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse API response as JSON: {e}")

        # Extract the generated text
        try:
            content = data["choices"][0]["message"]["content"]
            if not content:
                raise LLMError("Empty response from API")
            return content
        except (KeyError, IndexError) as e:
            raise LLMError(f"Unexpected API response structure: {e}")

    def _should_retry_attempt(self, attempt: int) -> bool:
        """Check if we should retry the current attempt"""
        return attempt < self.MAX_RETRIES - 1

    def _handle_retry_delay(self, exception: Exception, attempt: int) -> None:
        """Handle the delay before retrying based on exception type"""
        # For retryable errors, use standard delay
        delay = self.RETRY_DELAY
        error_type = type(exception).__name__
        logger.warning(f"{error_type}, retrying in {delay}s... (attempt {attempt + 1}/{self.MAX_RETRIES})")
        time.sleep(delay)

    def get_model_name(self) -> str:
        """
        Return the configured model name
        """
        return self.model