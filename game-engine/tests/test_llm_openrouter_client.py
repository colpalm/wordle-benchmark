import json
from unittest.mock import Mock, patch

import pytest
import requests

from llm_integration.llm_client import (
    LLMAuthenticationError,
    LLMError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from llm_integration.openrouter_client import OpenRouterClient


class TestOpenRouterClient:
    """Unit tests for OpenRouter client that don't require external API calls"""

    @pytest.fixture
    def client(self):
        """Returns an OpenRouterClient instance for testing"""
        return OpenRouterClient(api_key="fake-key", model="openai/gpt-4o-mini")

    def test_get_model_name(self, client):
        """Return the model name"""
        assert client.get_model_name() == "openai/gpt-4o-mini"

    @pytest.mark.parametrize("input_content,expected_output", [
        ("CRANE", "CRANE"),  # Simple response
        ('{"reasoning": "test", "guess": "CRANE"}', '{"reasoning": "test", "guess": "CRANE"}'),  # JSON response
    ])
    @patch('llm_integration.openrouter_client.requests.post')
    def test_successful_response(self, mock_post, client, input_content, expected_output):
        """Test successful API response with realistic Wordle JSON output"""
        # Mock successful response with realistic Wordle JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": input_content
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = client.generate_response("What's your guess?")

        # The client should return the raw string - parsing happens in ResponseParser
        assert result == expected_output

        # Verify the API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Check URL
        assert call_args[0][0] == "https://openrouter.ai/api/v1/chat/completions"

        # Check headers
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer fake-key"
        assert headers["Content-Type"] == "application/json"

        # Check payload structure
        payload = call_args[1]["json"]
        assert payload["model"] == "openai/gpt-4o-mini"
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][0]["content"] == "What's your guess?"
        assert "temperature" in payload
        assert "max_tokens" in payload

    @pytest.mark.parametrize("input_content,expected_output", [
        ("  CRANE  \n", "CRANE"),  # Simple response
        ('  {"reasoning": "test", "guess": "CRANE"}  \n', '{"reasoning": "test", "guess": "CRANE"}'),  # JSON response
    ])
    @patch('llm_integration.openrouter_client.requests.post')
    def test_response_whitespace_stripped(self, mock_post, client, input_content, expected_output):
        """Test that response whitespace is stripped for both simple and JSON responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": input_content
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = client.generate_response("What's your guess?")
        assert result == expected_output

    @patch('llm_integration.openrouter_client.requests.post')
    def test_authentication_error(self, mock_post, client):
        """Test handling of authentication errors (401)"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Client Error")
        mock_post.return_value = mock_response

        with pytest.raises(LLMAuthenticationError, match="Invalid API key"):
            client.generate_response("test")

    @patch('llm_integration.openrouter_client.requests.post')
    def test_quota_exceeded_error(self, mock_post, client):
        """Test handling of quota exceeded errors (402)"""
        mock_response = Mock()
        mock_response.status_code = 402
        mock_post.return_value = mock_response

        with pytest.raises(LLMQuotaExceededError, match="Quota or credits exhausted"):
            client.generate_response("test")

    @patch('llm_integration.openrouter_client.requests.post')
    @patch('llm_integration.openrouter_client.time.sleep')  # Mock sleep to speed up tests
    def test_rate_limit_with_retry_success(self, mock_sleep, mock_post, client):
        """Test rate limiting with successful retry"""
        # The first call returns 429, the second call succeeds
        mock_response_1 = Mock()
        mock_response_1.status_code = 429

        mock_response_2 = Mock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {
            "choices": [{"message": {"content": "CRANE"}}]
        }

        mock_post.side_effect = [mock_response_1, mock_response_2]

        result = client.generate_response("test")

        assert result == "CRANE"
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once()  # Should have slept between retries

    @patch('llm_integration.openrouter_client.requests.post')
    @patch('llm_integration.openrouter_client.time.sleep')
    def test_rate_limit_max_retries_exceeded(self, mock_sleep, mock_post, client):
        """Test rate limiting when max retries are exceeded"""
        # All calls return 429
        mock_response = Mock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        with pytest.raises(LLMRateLimitError, match="Rate limit exceeded after retries"):
            client.generate_response("test")

        assert mock_post.call_count == OpenRouterClient.MAX_RETRIES

    @patch('llm_integration.openrouter_client.requests.post')
    def test_other_http_error(self, mock_post, client):
        """Test handling of other HTTP errors (e.g., 500)"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
        mock_post.return_value = mock_response

        with pytest.raises(LLMError, match="HTTP error 500"):
            client.generate_response("test")

    @patch('llm_integration.openrouter_client.requests.post')
    @patch('llm_integration.openrouter_client.time.sleep')
    def test_timeout_error(self, mock_sleep, mock_post, client):
        # """Test handling of timeout errors"""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(LLMTimeoutError, match="Request timed out after"):
            client.generate_response("test")

        # Verify retry behavior
        assert mock_post.call_count == 3  # MAX_RETRIES
        assert mock_sleep.call_count == 2  # Should sleep between retries (3 attempts = 2 sleeps)

    @patch('llm_integration.openrouter_client.requests.post')
    @patch('llm_integration.openrouter_client.time.sleep')
    def test_timeout_with_retry_success(self, mock_sleep, mock_post, client):
        """Test timeout with successful retry"""
        # First call times out, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "CRANE"}}]
        }

        mock_post.side_effect = [
            requests.exceptions.Timeout("Request timed out"),
            mock_response
        ]

        result = client.generate_response("test")

        assert result == "CRANE"
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once()

    @patch('llm_integration.openrouter_client.requests.post')
    def test_json_decode_error(self, mock_post, client):
        """Test handling of invalid JSON responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_post.return_value = mock_response

        with pytest.raises(LLMError, match="Failed to parse API response as JSON"):
            client.generate_response("test")

    @patch('llm_integration.openrouter_client.requests.post')
    def test_unexpected_response_structure(self, mock_post, client):
        """Test handling of unexpected API response structure"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "unexpected": "structure"
        }
        mock_post.return_value = mock_response

        with pytest.raises(LLMError, match="Unexpected API response structure"):
            client.generate_response("test")

    @patch('llm_integration.openrouter_client.requests.post')
    def test_empty_response_content(self, mock_post, client):
        """Test handling of empty response content"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": ""
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        with pytest.raises(LLMError, match="Empty response from API"):
            client.generate_response("test")

    @patch('llm_integration.openrouter_client.requests.post')
    def test_request_exception(self, mock_post, client):
        """Test handling of general request exceptions"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(LLMError, match="Connection failed"):
            client.generate_response("test")

    @patch('llm_integration.openrouter_client.requests.post')
    @patch('llm_integration.openrouter_client.time.sleep')
    def test_exponential_backoff(self, mock_sleep, mock_post, client):
        """Test that exponential backoff is used for retries"""
        # All calls return 429 to trigger rate limit retries
        mock_response = Mock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        with pytest.raises(LLMRateLimitError):
            client.generate_response("test")

        # Verify exponential backoff for rate limits: should sleep 15s, then 30s
        expected_delays = [15.0, 30.0]
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays

    def test_no_retry_for_auth_errors(self):
        """Test that authentication errors are not retried"""
        with patch('llm_integration.openrouter_client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_post.return_value = mock_response

            client = OpenRouterClient(api_key="fake-key", model="openai/gpt-4o-mini")

            with pytest.raises(LLMAuthenticationError):
                client.generate_response("test")

            # Should only be called once (no retries)
            assert mock_post.call_count == 1

    def test_no_retry_for_quota_errors(self):
        """Test that quota exceeded errors are not retried"""
        with patch('llm_integration.openrouter_client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 402
            mock_post.return_value = mock_response

            client = OpenRouterClient(api_key="fake-key", model="openai/gpt-4o-mini")

            with pytest.raises(LLMQuotaExceededError):
                client.generate_response("test")

            # Should only be called once (no retries)
            assert mock_post.call_count == 1

    @patch('llm_integration.openrouter_client.requests.post')
    def test_cost_calculation_with_usage_data(self, mock_post, client):
        """Test that cost is calculated correctly when usage data is provided"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "CRANE"}}],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
        mock_post.return_value = mock_response

        result = client.generate_response("test")

        assert result == "CRANE"

        # Verify usage data is tracked
        usage_stats = client.get_current_usage_stats()
        assert usage_stats["prompt_tokens"] == mock_response.json.return_value["usage"]["prompt_tokens"]
        assert usage_stats["completion_tokens"] == mock_response.json.return_value["usage"]["completion_tokens"]
        assert usage_stats["total_tokens"] == mock_response.json.return_value["usage"]["total_tokens"]

        # Verify cost calculation (gpt-4o-mini: $0.15/$0.60 per 1M tokens)
        # Expected: (100/1M * 0.15) + (50/1M * 0.60) = 0.000015 + 0.00003 = 0.000045
        expected_cost = (100/1_000_000 * 0.15) + (50/1_000_000 * 0.60)
        assert usage_stats["cost_usd"] == pytest.approx(expected_cost)

    @patch('llm_integration.openrouter_client.requests.post')
    def test_cost_calculation_with_reasoning_tokens(self, mock_post):
        """Test cost calculation when reasoning tokens are present (e.g., O3 model)"""
        client = OpenRouterClient(api_key="fake-key", model="openai/o3")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "CRANE"}}],
            "usage": {
                "prompt_tokens": 500,
                "completion_tokens": 50,
                "reasoning_tokens": 2000,
                "total_tokens": 2550
            }
        }
        mock_post.return_value = mock_response

        result = client.generate_response("test")

        assert result == "CRANE"

        # Verify usage data tracking
        usage_stats = client.get_current_usage_stats()
        assert usage_stats["prompt_tokens"] == mock_response.json.return_value["usage"]["prompt_tokens"]
        assert usage_stats["completion_tokens"] == mock_response.json.return_value["usage"]["completion_tokens"]
        assert usage_stats["reasoning_tokens"] == mock_response.json.return_value["usage"]["reasoning_tokens"]
        assert usage_stats["total_tokens"] == mock_response.json.return_value["usage"]["total_tokens"]

        # Verify cost calculation (O3: $2.0/$8.0 per 1M tokens)
        # Expected: (500/1M * 2.0) + ((50 + 2000)/1M * 8.0) = 0.001 + 0.0164 = 0.0174
        expected_cost = (500/1_000_000 * 2.0) + ((50 + 2000)/1_000_000 * 8.0)
        assert usage_stats["cost_usd"] == pytest.approx(expected_cost)

    @patch('llm_integration.openrouter_client.requests.post')
    def test_cost_calculation_no_usage_data(self, mock_post, client):
        """Test that cost is reset when no usage data is provided"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "CRANE"}}]
            # No usage data
        }
        mock_post.return_value = mock_response

        result = client.generate_response("test")

        assert result == "CRANE"

        # All usage metrics should be reset to 0
        usage_stats = client.get_current_usage_stats()
        assert usage_stats["prompt_tokens"] == 0
        assert usage_stats["completion_tokens"] == 0
        assert usage_stats["reasoning_tokens"] == 0
        assert usage_stats["total_tokens"] == 0
        assert usage_stats["cost_usd"] == pytest.approx(0.0)

    @patch('llm_integration.openrouter_client.requests.post')
    def test_cost_calculation_unknown_model_raises_error(self, mock_post):
        """Test that unknown models raise pricing errors"""
        client = OpenRouterClient(api_key="fake-key", model="unknown/model")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "CRANE"}}],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Pricing not available for model: unknown/model"):
            client.generate_response("test")
