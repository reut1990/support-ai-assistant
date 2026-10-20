"""Prices and cost estimates, so nothing runs without the user knowing the cost first."""

# US dollars per million tokens (input, output), Anthropic API prices as of October 2026.
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}

# Rough sizes used for the estimate before any call is made.
CHARS_PER_TOKEN = 4
EXPECTED_OUTPUT_TOKENS = 300  # the answer plus the model's short reasoning


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICES[model]
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


def estimate_ticket_tokens(system_prompt: str, message: str) -> tuple[int, int]:
    input_tokens = (len(system_prompt) + len(message)) // CHARS_PER_TOKEN + 50
    return input_tokens, EXPECTED_OUTPUT_TOKENS


def estimate_run(model: str, system_prompt: str, messages: list[str]) -> float:
    total = 0.0
    for m in messages:
        tokens_in, tokens_out = estimate_ticket_tokens(system_prompt, m)
        total += cost_usd(model, tokens_in, tokens_out)
    return total
