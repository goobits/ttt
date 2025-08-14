"""Pytest configuration file."""

import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import pytest
from dotenv import load_dotenv

# Add the parent directory and src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


# Configuration for rate limiting delays
OPENROUTER_DEFAULT_DELAY = 1.0  # Default 1 second delay between OpenRouter API calls
OPENAI_DEFAULT_DELAY = 0.5  # Default 0.5 second delay between OpenAI API calls
ANTHROPIC_DEFAULT_DELAY = 0.5  # Default 0.5 second delay between Anthropic API calls
CONSERVATIVE_DEFAULT_DELAY = 1.0  # Conservative default delay for unknown providers

# Smart rate limiting configuration
MIN_DELAY = 0.1  # Minimum delay for progressive rate limiting
MAX_DELAY = 2.0  # Maximum delay for progressive rate limiting


def _should_skip_rate_limiting():
    """Determine if rate limiting should be skipped based on environment.
    
    Returns True if:
    - Running in CI environment
    - No real API keys present (all tests would be mocked)
    - Explicit disable flag is set
    - Running unit tests only
    """
    # Check for CI environment
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") or os.getenv("PYTEST_DISABLE_RATE_LIMIT"):
        return True
    
    # Check if any real API keys are present
    has_real_keys = any([
        _is_valid_api_key(os.getenv("OPENAI_API_KEY")),
        _is_valid_api_key(os.getenv("ANTHROPIC_API_KEY")),
        _is_valid_api_key(os.getenv("OPENROUTER_API_KEY")),
        _is_valid_api_key(os.getenv("GOOGLE_API_KEY"))
    ])
    
    # If no real API keys, all tests are mocked - skip delays
    return not has_real_keys


def _is_valid_api_key(key):
    """Check if an API key looks real (not a test key)."""
    if not key:
        return False
    key_lower = key.lower()
    # Common test/mock key patterns
    test_patterns = ["test", "mock", "fake", "demo", "example", "dummy"]
    return len(key) > 10 and not any(pattern in key_lower for pattern in test_patterns)


def _uses_mock_backend(request):
    """Check if the test is using a mock backend by examining fixtures and test content."""
    # Check if mock-related fixtures are used
    if hasattr(request, 'fixturenames'):
        mock_fixtures = [name for name in request.fixturenames if 'mock' in name.lower()]
        if mock_fixtures:
            return True
    
    # Check test function for mock usage
    if hasattr(request.node, 'function') and hasattr(request.node.function, '__code__'):
        code_names = request.node.function.__code__.co_names
        mock_indicators = ['mock', 'Mock', 'patch', 'MagicMock']
        if any(indicator in code_names for indicator in mock_indicators):
            return True
    
    return False


@pytest.fixture
def rate_limit_delay(request):
    """Fixture to add delays between API calls to respect rate limits.

    Returns a function that adds appropriate delay based on the provider.
    Uses smart detection to skip delays when appropriate.
    """
    # Track delay counts for progressive limiting
    delay_count = 0
    
    def delay(provider=None, force=False):
        """Add delay based on provider to respect rate limits.

        Args:
            provider: The API provider name (openrouter, openai, anthropic, etc.)
                     If None, uses a conservative default delay.
            force: Force delay even if conditions suggest skipping
        """
        nonlocal delay_count
        
        # Skip delays in various conditions unless forced
        if not force:
            if _should_skip_rate_limiting():
                return
            if _uses_mock_backend(request):
                return
        
        # Calculate progressive delay
        if provider:
            provider_lower = provider.lower()
            if "openrouter" in provider_lower:
                base_delay = float(os.getenv("OPENROUTER_RATE_DELAY", OPENROUTER_DEFAULT_DELAY))
            elif "openai" in provider_lower or "gpt" in provider_lower:
                base_delay = float(os.getenv("OPENAI_RATE_DELAY", OPENAI_DEFAULT_DELAY))
            elif "anthropic" in provider_lower or "claude" in provider_lower:
                base_delay = float(os.getenv("ANTHROPIC_RATE_DELAY", ANTHROPIC_DEFAULT_DELAY))
            else:
                base_delay = CONSERVATIVE_DEFAULT_DELAY
        else:
            base_delay = CONSERVATIVE_DEFAULT_DELAY
        
        # Progressive delay: start small, increase if needed
        delay_multiplier = min(1.0 + (delay_count * 0.1), 2.0)  # Max 2x original delay
        actual_delay = max(MIN_DELAY, min(base_delay * delay_multiplier, MAX_DELAY))
        
        delay_count += 1
        time.sleep(actual_delay)

    return delay


@pytest.fixture(autouse=True)
def auto_rate_limit_for_integration_tests(request, rate_limit_delay):
    """Automatically add delays for integration tests that need real API calls.

    Uses smart detection to only delay tests that actually make API calls.
    """
    # Check if this is an integration test
    markers = request.node.iter_markers(name="integration")
    if not list(markers):
        return
    
    # Skip delays if conditions indicate this test doesn't need them
    if _should_skip_rate_limiting():
        return
        
    # Skip if test uses mocks
    if _uses_mock_backend(request):
        return
    
    # Check if test function explicitly uses --real-api flag
    real_api_flag = request.config.getoption("--real-api", default=False)
    if not real_api_flag and not any([
        _is_valid_api_key(os.getenv("OPENAI_API_KEY")),
        _is_valid_api_key(os.getenv("ANTHROPIC_API_KEY")),
        _is_valid_api_key(os.getenv("OPENROUTER_API_KEY"))
    ]):
        return
    
    # Add a minimal initial delay for real integration tests
    time.sleep(MIN_DELAY)


@pytest.fixture
def delayed_ask(rate_limit_delay):
    """Wrapper for the ask function that adds rate limit delays.

    Usage in tests:
        response = delayed_ask("Hello", model="gpt-3.5-turbo")
    """
    from ttt import ask

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
    from ttt import stream

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
    from ttt import chat

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
