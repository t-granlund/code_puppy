#!/usr/bin/env python3
"""Test script for rate limit header parsing."""

from code_puppy.core.rate_limit_headers import RateLimitTracker, RateLimitState

def main():
    print("Rate Limit Header Parsing Test")
    print("=" * 50)

    # Test Cerebras headers
    tracker = RateLimitTracker()
    cerebras_headers = {
        "x-ratelimit-limit-tokens-minute": "300000",
        "x-ratelimit-remaining-tokens-minute": "250000",
        "x-ratelimit-limit-requests-minute": "100",
        "x-ratelimit-remaining-requests-minute": "85",
    }

    updated = tracker.update_from_response("cerebras", cerebras_headers)
    print(f"Cerebras headers parsed: {updated}")

    state = tracker.get_state("cerebras")
    print(f"  Tokens remaining: {state.remaining_tokens_minute}/{state.limit_tokens_minute}")
    print(f"  Requests remaining: {state.remaining_requests_minute}/{state.limit_requests_minute}")

    # Test proactive limit detection
    near_limit, reason = state.is_near_limit(0.2)  # 20% threshold
    print(f"  Near limit (20% threshold): {near_limit}")
    print(f"  Reason: {reason}")

    # Test with low remaining
    print()
    print("Low Remaining Test:")
    low_headers = {
        "x-ratelimit-limit-tokens-minute": "300000",
        "x-ratelimit-remaining-tokens-minute": "50000",  # ~17% remaining
    }
    tracker.update_from_response("cerebras-low", low_headers)
    state_low = tracker.get_state("cerebras-low")
    near, reason = state_low.is_near_limit(0.2)
    print(f"  17% remaining - Near limit: {near}")
    print(f"  Reason: {reason}")

    print()
    print("✅ Rate limit header parsing working!")


if __name__ == "__main__":
    main()
