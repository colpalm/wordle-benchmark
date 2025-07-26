from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    """Pricing information for a specific model"""
    input_cost_per_1m: float
    output_cost_per_1m: float

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int, reasoning_tokens: int = 0) -> float:
        """Calculate the total cost for a given prompt and response"""
        input_cost = (prompt_tokens / 1_000_000) * self.input_cost_per_1m

        # Assuming reasoning tokens are billed as output tokens
        total_output_tokens = completion_tokens + reasoning_tokens
        output_cost = (total_output_tokens / 1_000_000) * self.output_cost_per_1m

        return input_cost + output_cost

    @staticmethod
    def get_model_pricing(model: str) -> "ModelPricing":
        """Get pricing information for a specific model"""
        if model not in MODEL_PRICING:
            available = ", ".join(MODEL_PRICING.keys())
            raise ValueError(f"Pricing not available for model: {model}. Available: {available}")
        return MODEL_PRICING[model]


# Pricing as of July 2025 - verify current rates periodically
# All values are USD per million tokens (input_cost_per_1m, output_cost_per_1m)
MODEL_PRICING: dict[str, ModelPricing] = {
    "openai/gpt-4o-mini": ModelPricing(0.15, 0.60),
    "openai/o3": ModelPricing(2.0, 8.0),
    "anthropic/claude-sonnet-4": ModelPricing(3.0, 15.0),
    "anthropic/claude-opus-4": ModelPricing(15.0, 75.0),
    "google/gemini-2.5-flash": ModelPricing(0.30, 2.5),
    "google/gemini-2.5-pro": ModelPricing(1.25, 10.0),
}
