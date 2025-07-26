import pytest
from llm_integration.pricing import ModelPricing


class TestModelPricing:
    """Unit tests for ModelPricing class"""

    def test_calculate_cost_basic(self):
        """Test basic cost calculation with prompt and completion tokens"""
        pricing = ModelPricing(input_cost_per_1m=1.0, output_cost_per_1m=2.0)
        
        # 100,000 prompt tokens + 50,000 completion tokens
        cost = pricing.calculate_cost(prompt_tokens=100_000, completion_tokens=50_000)
        
        # Expected: (100,000 / 1,000,000) * 1.0 + (50,000 / 1,000,000) * 2.0
        # = 0.1 + 0.1 = 0.2
        expected = (100_000 / 1_000_000) * 1.0 + (50_000 / 1_000_000) * 2.0
        assert cost == pytest.approx(expected)

    def test_calculate_cost_with_reasoning_tokens(self):
        """Test cost calculation including reasoning tokens"""
        pricing = ModelPricing(input_cost_per_1m=1.0, output_cost_per_1m=3.0)
        
        # 100,000 prompt + 30,000 completion + 20,000 reasoning tokens
        cost = pricing.calculate_cost(
            prompt_tokens=100_000, 
            completion_tokens=30_000, 
            reasoning_tokens=20_000
        )
        
        # Expected: (100,000 / 1,000,000) * 1.0 + ((30,000 + 20,000) / 1,000,000) * 3.0
        # = 0.1 + 0.15 = 0.25
        expected = (100_000 / 1_000_000) * 1.0 + ((30_000 + 20_000) / 1_000_000) * 3.0
        assert cost == pytest.approx(expected)

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens"""
        pricing = ModelPricing(input_cost_per_1m=1.0, output_cost_per_1m=2.0)

        cost = pricing.calculate_cost(prompt_tokens=0, completion_tokens=0)

        assert cost == pytest.approx(0.0)

    @pytest.mark.parametrize("model,expected_input,expected_output", [
        ("openai/gpt-4o-mini", 0.15, 0.60),
        ("openai/o3", 2.0, 8.0),
        ("anthropic/claude-sonnet-4", 3.0, 15.0),
        ("anthropic/claude-opus-4", 15.0, 75.0),
        ("google/gemini-2.5-flash", 0.30, 2.5),
        ("google/gemini-2.5-pro", 1.25, 10.0),
    ])
    def test_get_model_pricing_known_models(self, model, expected_input, expected_output):
        """Test getting pricing for all known models"""
        pricing = ModelPricing.get_model_pricing(model)
        
        assert pricing.input_cost_per_1m == expected_input
        assert pricing.output_cost_per_1m == expected_output

    def test_get_model_pricing_unknown_model(self):
        """Test error handling for unknown models"""
        with pytest.raises(ValueError, match="Pricing not available for model: unknown/model"):
            ModelPricing.get_model_pricing("unknown/model")

    def test_get_model_pricing_error_includes_available_models(self):
        """Test that error message includes list of available models"""
        with pytest.raises(ValueError) as exc_info:
            ModelPricing.get_model_pricing("unknown/model")
        
        error_message = str(exc_info.value)
        assert "Available:" in error_message
        assert "openai/gpt-4o-mini" in error_message
        assert "anthropic/claude-sonnet-4" in error_message