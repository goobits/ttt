#!/usr/bin/env python3
"""
Exception handling examples for the AI library.

This example demonstrates how to handle various exceptions
that can be raised by the library.
"""

import ai
from ai import (
    ask,
    chat,
    PersistentChatSession,
    configure,
    # Import all exception types
    AIError,
    BackendNotAvailableError,
    BackendConnectionError,
    BackendTimeoutError,
    ModelNotFoundError,
    ModelNotSupportedError,
    APIKeyError,
    ConfigFileError,
    InvalidPromptError,
    InvalidParameterError,
    EmptyResponseError,
    MultiModalError,
    RateLimitError,
    QuotaExceededError,
    SessionLoadError,
    SessionSaveError,
)
from pathlib import Path
import os


def handle_backend_errors():
    """Demonstrate handling backend-related errors."""
    print("=== Backend Error Handling ===\n")

    # 1. Backend not available
    try:
        response = ask("Hello", backend="nonexistent")
    except BackendNotAvailableError as e:
        print(f"Backend not available: {e}")
        print(f"  Details: {e.details}")

    # 2. Backend connection error (simulated by using wrong URL)
    try:
        # Temporarily configure wrong URL
        configure(ollama_base_url="http://localhost:99999")
        response = ask("Hello", backend="local")
    except BackendConnectionError as e:
        print(f"\nConnection error: {e}")
        print(f"  Backend: {e.details.get('backend')}")
    except Exception as e:
        # In case it's wrapped in another exception
        print(f"\nUnexpected error: {type(e).__name__}: {e}")
    finally:
        # Reset to default
        configure(ollama_base_url="http://localhost:11434")


def handle_model_errors():
    """Demonstrate handling model-related errors."""
    print("\n=== Model Error Handling ===\n")

    # 1. Model not found
    try:
        response = ask("Hello", model="nonexistent-model-xyz")
    except ModelNotFoundError as e:
        print(f"Model not found: {e}")
        print(f"  Model: {e.details.get('model')}")
        print(f"  Backend: {e.details.get('backend')}")

    # 2. Model doesn't support feature (multi-modal on local)
    try:
        from ai import ImageInput

        response = ask(
            ["What's in this image?", ImageInput("test.jpg")], backend="local"
        )
    except MultiModalError as e:
        print(f"\nMulti-modal error: {e}")
        print(f"  Reason: {e.details.get('reason')}")


def handle_api_key_errors():
    """Demonstrate handling API key errors."""
    print("\n=== API Key Error Handling ===\n")

    # Save current API key
    original_key = os.environ.get("OPENAI_API_KEY")

    try:
        # Set invalid API key
        os.environ["OPENAI_API_KEY"] = "invalid-key-123"

        response = ask("Hello", model="gpt-3.5-turbo", backend="cloud")
    except APIKeyError as e:
        print(f"API key error: {e}")
        print(f"  Provider: {e.details.get('provider')}")
        print(f"  Environment variable: {e.details.get('env_var')}")
    except Exception as e:
        # Some errors might be wrapped
        print(f"Error (may be API key related): {type(e).__name__}: {e}")
    finally:
        # Restore original key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)


def handle_rate_limit_errors():
    """Demonstrate handling rate limit errors."""
    print("\n=== Rate Limit Error Handling ===\n")

    # This would typically happen with rapid requests
    print("Rate limit errors occur when making too many requests.")
    print("Example handling:")
    print(
        """
    try:
        for i in range(100):
            response = ask(f"Question {i}", model="gpt-3.5-turbo")
    except RateLimitError as e:
        print(f"Rate limited: {e}")
        retry_after = e.details.get('retry_after')
        if retry_after:
            print(f"Retry after {retry_after} seconds")
            time.sleep(retry_after)
    """
    )


def handle_session_errors():
    """Demonstrate handling session-related errors."""
    print("\n=== Session Error Handling ===\n")

    # 1. Load non-existent session
    try:
        session = PersistentChatSession.load("nonexistent_session.json")
    except SessionLoadError as e:
        print(f"Session load error: {e}")
        print(f"  File: {e.details.get('file_path')}")
        print(f"  Reason: {e.details.get('reason')}")

    # 2. Save to invalid location
    try:
        with chat(persist=True) as session:
            session.ask("Hello")
            # Try to save to a directory that doesn't exist
            session.save("/nonexistent/directory/session.json")
    except SessionSaveError as e:
        print(f"\nSession save error: {e}")
        print(f"  File: {e.details.get('file_path')}")
        print(f"  Reason: {e.details.get('reason')}")

    # 3. Invalid save format
    try:
        with chat(persist=True) as session:
            session.save("test.json", format="invalid")
    except InvalidParameterError as e:
        print(f"\nInvalid parameter: {e}")
        print(f"  Parameter: {e.details.get('parameter')}")
        print(f"  Value: {e.details.get('value')}")
        print(f"  Reason: {e.details.get('reason')}")


def handle_config_errors():
    """Demonstrate handling configuration errors."""
    print("\n=== Configuration Error Handling ===\n")

    # Create an invalid config file
    invalid_config = Path("invalid_config.yaml")
    invalid_config.write_text("invalid: yaml: content: [}")

    try:
        from ai.config import load_config

        config = load_config(invalid_config)
    except ConfigFileError as e:
        print(f"Config file error: {e}")
        print(f"  File: {e.details.get('file_path')}")
        print(f"  Reason: {e.details.get('reason')}")
    finally:
        # Clean up
        invalid_config.unlink()


def handle_generic_errors():
    """Demonstrate handling generic AI errors."""
    print("\n=== Generic Error Handling ===\n")

    print("You can catch all AI library errors with AIError:")
    print(
        """
    try:
        response = ask("Question", model="unknown", backend="invalid")
    except AIError as e:
        # This catches any error from the AI library
        print(f"AI Error: {type(e).__name__}: {e}")
        print(f"Details: {e.details}")
    """
    )


def best_practices():
    """Show best practices for error handling."""
    print("\n=== Best Practices ===\n")

    print("1. Be specific when you know what errors to expect:")
    print(
        """
    try:
        response = ask("Hello", model=user_specified_model)
    except ModelNotFoundError:
        # Suggest available models
        print("Available models: gpt-3.5-turbo, gpt-4, claude-3-sonnet")
    except APIKeyError as e:
        # Guide user to set up API key
        print(f"Please set {e.details['env_var']} environment variable")
    """
    )

    print("\n2. Use AIError as a catch-all for any library error:")
    print(
        """
    try:
        response = ask(prompt)
    except AIError as e:
        logger.error(f"AI operation failed: {e}")
        # Fallback behavior
    """
    )

    print("\n3. Access error details for better handling:")
    print(
        """
    try:
        response = ask(prompt, backend=backend)
    except BackendConnectionError as e:
        backend_name = e.details.get('backend')
        original_error = e.details.get('original_error')
        # Implement retry logic or fallback
    """
    )

    print("\n4. Let unexpected errors bubble up in development:")
    print(
        """
    try:
        response = ask(prompt)
    except AIError:
        # Handle expected AI library errors
        pass
    # Don't catch Exception unless you log and re-raise
    """
    )


def main():
    """Run all examples."""
    print("AI Library Exception Handling Examples\n")
    print("=" * 50)

    handle_backend_errors()
    handle_model_errors()
    handle_api_key_errors()
    handle_rate_limit_errors()
    handle_session_errors()
    handle_config_errors()
    handle_generic_errors()
    best_practices()

    print("\n" + "=" * 50)
    print("\nException handling examples complete!")
    print("\nKey takeaways:")
    print("- Use specific exceptions when you know what to expect")
    print("- AIError catches all library-specific errors")
    print("- Access e.details for additional context")
    print("- Provide helpful error messages to users")


if __name__ == "__main__":
    main()
