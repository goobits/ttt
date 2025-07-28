"""Pytest configuration file."""

import os
import sys
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


# Configuration for rate limiting delays
OPENROUTER_DEFAULT_DELAY = 1.0  # Default 1 second delay between OpenRouter API calls
OPENAI_DEFAULT_DELAY = 0.5  # Default 0.5 second delay between OpenAI API calls
ANTHROPIC_DEFAULT_DELAY = 0.5  # Default 0.5 second delay between Anthropic API calls


@pytest.fixture
def rate_limit_delay():
    """Fixture to add delays between API calls to respect rate limits.

    Returns a function that adds appropriate delay based on the provider.
    """

    def delay(provider=None):
        """Add delay based on provider to respect rate limits.

        Args:
            provider: The API provider name (openrouter, openai, anthropic, etc.)
                     If None, uses a conservative default delay.
        """
        if provider:
            provider_lower = provider.lower()
            if "openrouter" in provider_lower:
                delay_time = float(
                    os.getenv("OPENROUTER_RATE_DELAY", OPENROUTER_DEFAULT_DELAY)
                )
            elif "openai" in provider_lower or "gpt" in provider_lower:
                delay_time = float(os.getenv("OPENAI_RATE_DELAY", OPENAI_DEFAULT_DELAY))
            elif "anthropic" in provider_lower or "claude" in provider_lower:
                delay_time = float(
                    os.getenv("ANTHROPIC_RATE_DELAY", ANTHROPIC_DEFAULT_DELAY)
                )
            else:
                # Conservative default for unknown providers
                delay_time = 1.0
        else:
            # Conservative default when no provider specified
            delay_time = 1.0

        time.sleep(delay_time)

    return delay


@pytest.fixture(autouse=True)
def auto_rate_limit_for_integration_tests(request, rate_limit_delay):
    """Automatically add delays for integration tests to prevent rate limiting.

    This fixture runs automatically for all tests marked with @pytest.mark.integration
    """
    # Check if this is an integration test
    markers = request.node.iter_markers(name="integration")
    if list(markers):
        # Add a small delay before each integration test
        # This helps prevent hitting rate limits when running multiple tests
        rate_limit_delay()


@pytest.fixture
def delayed_ask(rate_limit_delay):
    """Wrapper for the ask function that adds rate limit delays.

    Usage in tests:
        response = delayed_ask("Hello", model="gpt-3.5-turbo")
    """
    from ai import ask

    def _delayed_ask(*args, **kwargs):
        # Extract model to determine provider
        model = kwargs.get("model", "")
        if model:
            if "openrouter" in model:
                rate_limit_delay("openrouter")
            elif "gpt" in model:
                rate_limit_delay("openai")
            elif "claude" in model:
                rate_limit_delay("anthropic")
            else:
                rate_limit_delay()
        else:
            rate_limit_delay()

        return ask(*args, **kwargs)

    return _delayed_ask


@pytest.fixture
def delayed_stream(rate_limit_delay):
    """Wrapper for the stream function that adds rate limit delays.

    Usage in tests:
        for chunk in delayed_stream("Hello", model="gpt-3.5-turbo"):
            print(chunk)
    """
    from ai import stream

    def _delayed_stream(*args, **kwargs):
        # Extract model to determine provider
        model = kwargs.get("model", "")
        if model:
            if "openrouter" in model:
                rate_limit_delay("openrouter")
            elif "gpt" in model:
                rate_limit_delay("openai")
            elif "claude" in model:
                rate_limit_delay("anthropic")
            else:
                rate_limit_delay()
        else:
            rate_limit_delay()

        return stream(*args, **kwargs)

    return _delayed_stream


@pytest.fixture
def delayed_chat(rate_limit_delay):
    """Wrapper for the chat function that adds rate limit delays.

    Usage in tests:
        with delayed_chat(model="gpt-3.5-turbo") as session:
            response = session.ask("Hello")
    """
    from contextlib import contextmanager

    from ai import chat

    class DelayedChatSession:
        def __init__(self, session, delay_func, model):
            self.session = session
            self.delay_func = delay_func
            self.model = model

        def ask(self, *args, **kwargs):
            # Add delay before each ask
            if "openrouter" in self.model:
                self.delay_func("openrouter")
            elif "gpt" in self.model:
                self.delay_func("openai")
            elif "claude" in self.model:
                self.delay_func("anthropic")
            else:
                self.delay_func()

            return self.session.ask(*args, **kwargs)

        def stream(self, *args, **kwargs):
            # Add delay before each stream
            if "openrouter" in self.model:
                self.delay_func("openrouter")
            elif "gpt" in self.model:
                self.delay_func("openai")
            elif "claude" in self.model:
                self.delay_func("anthropic")
            else:
                self.delay_func()

            return self.session.stream(*args, **kwargs)

        def clear(self):
            return self.session.clear()

    @contextmanager
    def _delayed_chat(*args, **kwargs):
        model = kwargs.get("model", "")

        # Add initial delay
        if "openrouter" in model:
            rate_limit_delay("openrouter")
        elif "gpt" in model:
            rate_limit_delay("openai")
        elif "claude" in model:
            rate_limit_delay("anthropic")
        else:
            rate_limit_delay()

        # Create chat session and wrap it
        with chat(*args, **kwargs) as session:
            yield DelayedChatSession(session, rate_limit_delay, model)

    return _delayed_chat


# Hook for customizing test collection
def pytest_collection_modifyitems(config, items):
    """Add markers and customize test collection."""
    for item in items:
        # Add integration marker based on test file name or function name
        if "integration" in item.nodeid or "test_integration" in item.module.__name__:
            item.add_marker(pytest.mark.integration)


# Command line options
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--real-api",
        action="store_true",
        default=False,
        help="Run tests that require real API keys",
    )
    parser.addoption(
        "--rate-delay",
        type=float,
        default=None,
        help="Override default rate limit delay (in seconds)",
    )
