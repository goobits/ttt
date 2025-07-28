# Rate Limiting Configuration for Integration Tests

This document describes the pytest fixtures and configuration available for managing rate limits when running integration tests that make real API calls.

## Overview

To prevent hitting API rate limits when running integration tests, we've implemented several pytest fixtures that automatically add delays between API calls. These delays are configurable and provider-specific.

## Default Rate Limits

Based on research and best practices for various providers:

- **OpenRouter**: 1.0 second delay (default)
- **OpenAI**: 0.5 second delay (default)
- **Anthropic**: 0.5 second delay (default)
- **Unknown providers**: 1.0 second delay (conservative default)

## Available Fixtures

### 1. `rate_limit_delay`

A basic fixture that provides a delay function:

```python
def test_with_manual_delay(rate_limit_delay):
    # Add delay for OpenRouter
    rate_limit_delay("openrouter")

    # Make API call
    response = ask("Hello", model="openrouter/google/gemini-2.5-flash")

    # Add delay for OpenAI
    rate_limit_delay("openai")

    # Make another API call
    response2 = ask("World", model="gpt-3.5-turbo")
```

### 2. `auto_rate_limit_for_integration_tests` (Automatic)

This fixture runs automatically for all tests marked with `@pytest.mark.integration`. It adds a delay before each integration test to prevent rapid successive calls.

```python
@pytest.mark.integration
def test_api_call():
    # Delay is automatically added before this test runs
    response = ask("Hello", model="gpt-3.5-turbo")
```

### 3. `delayed_ask`

A wrapper around the `ask` function that automatically adds appropriate delays:

```python
def test_with_delayed_ask(delayed_ask):
    # Automatically adds delay based on model
    response = delayed_ask("Hello", model="openrouter/google/gemini-2.5-flash")
    assert response.succeeded

    # Multiple calls will each have delays
    response2 = delayed_ask("World", model="gpt-3.5-turbo")
    assert response2.succeeded
```

### 4. `delayed_stream`

A wrapper around the `stream` function with automatic delays:

```python
def test_with_delayed_stream(delayed_stream):
    chunks = []
    # Automatically adds delay before streaming
    for chunk in delayed_stream("Count to 3", model="gpt-3.5-turbo"):
        chunks.append(chunk)

    assert len(chunks) > 0
```

### 5. `delayed_chat`

A wrapper around the `chat` function for session-based conversations:

```python
def test_with_delayed_chat(delayed_chat):
    with delayed_chat(model="gpt-3.5-turbo") as session:
        # Each ask() call will have automatic delays
        response1 = session.ask("My name is Alice")
        response2 = session.ask("What's my name?")

        assert "Alice" in str(response2)
```

## Configuration

### Environment Variables

You can override default delays using environment variables:

```bash
# Set custom delays for each provider
export OPENROUTER_RATE_DELAY=2.0  # 2 seconds for OpenRouter
export OPENAI_RATE_DELAY=1.0      # 1 second for OpenAI
export ANTHROPIC_RATE_DELAY=0.3   # 0.3 seconds for Anthropic

# Run tests with custom delays
pytest tests/test_integration.py -k "integration"
```

### Command Line Options

Override delays via command line:

```bash
# Set a global rate delay for all providers
pytest tests/test_integration.py --rate-delay 1.5
```

## Usage Examples

### Example 1: Simple Integration Test

```python
@pytest.mark.integration
def test_basic_api_call(delayed_ask):
    """Test with automatic rate limiting."""
    response = delayed_ask(
        "What is 2+2?",
        model="openrouter/google/gemini-2.5-flash"
    )
    assert "4" in str(response)
```

### Example 2: Multiple Provider Test

```python
@pytest.mark.integration
def test_multiple_providers(delayed_ask):
    """Test multiple providers with appropriate delays."""
    providers = [
        ("openrouter/google/gemini-2.5-flash", "OpenRouter test"),
        ("gpt-3.5-turbo", "OpenAI test"),
        ("claude-3-haiku-20240307", "Anthropic test")
    ]

    for model, prompt in providers:
        response = delayed_ask(prompt, model=model)
        assert response.succeeded
```

### Example 3: Stress Test with Rate Limiting

```python
@pytest.mark.integration
@pytest.mark.slow
def test_stress_with_rate_limits(delayed_ask, rate_limit_delay):
    """Stress test with proper rate limiting."""
    responses = []

    # Make 10 rapid requests with delays
    for i in range(10):
        # delayed_ask automatically adds provider-specific delay
        response = delayed_ask(
            f"Request {i}",
            model="openrouter/google/gemini-2.5-flash"
        )
        responses.append(response)

        # Add extra delay every 5 requests
        if i % 5 == 4:
            rate_limit_delay("openrouter")

    # Verify all succeeded
    assert all(r.succeeded for r in responses)
```

## Best Practices

1. **Use delayed fixtures by default**: When writing integration tests, prefer `delayed_ask`, `delayed_stream`, and `delayed_chat` over the raw functions.

2. **Mark integration tests**: Always mark integration tests with `@pytest.mark.integration` to benefit from automatic delays.

3. **Configure for your usage**: If you have higher rate limits, adjust the delays via environment variables to speed up tests.

4. **Add extra delays for stress tests**: For tests that make many rapid requests, add additional delays using `rate_limit_delay()`.

5. **Monitor for rate limit errors**: Even with delays, watch for `RateLimitError` exceptions and adjust delays accordingly.

## Running Integration Tests

```bash
# Run all integration tests with rate limiting
pytest tests/test_integration.py -v

# Run with custom delay
OPENROUTER_RATE_DELAY=2.0 pytest tests/test_integration.py

# Run specific test class
pytest tests/test_integration.py::TestRealAPIIntegration -v

# Run with real API keys only
pytest tests/test_integration.py --real-api
```

## Troubleshooting

### Still hitting rate limits?

1. Increase the delay for the problematic provider:
   ```bash
   export OPENROUTER_RATE_DELAY=3.0
   ```

2. Add manual delays in your test:
   ```python
   def test_heavy_usage(rate_limit_delay, delayed_ask):
       for i in range(20):
           response = delayed_ask("Test", model="openrouter/model")
           if i % 10 == 9:
               # Extra delay every 10 requests
               rate_limit_delay("openrouter")
   ```

3. Use the `--rate-delay` command line option for a quick test:
   ```bash
   pytest tests/test_integration.py --rate-delay 2.5
   ```

### Tests running too slowly?

If you have high rate limits or paid tiers, reduce the delays:

```bash
export OPENROUTER_RATE_DELAY=0.2
export OPENAI_RATE_DELAY=0.1
export ANTHROPIC_RATE_DELAY=0.1
```

Or disable delays entirely (not recommended):

```bash
export OPENROUTER_RATE_DELAY=0
```
