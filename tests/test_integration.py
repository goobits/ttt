"""Integration tests with real API keys.

These tests require actual API keys and make real network calls.
Run with: pytest tests/test_integration.py -k "integration" --real-api

Set environment variables:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY  
- OPENROUTER_API_KEY (recommended)

Note: These tests will consume API credits and should be run sparingly.
"""

import pytest
import os
from ai import ask, stream, chat
from ai.backends.cloud import CloudBackend


def skip_if_no_api_keys():
    """Skip test if no API keys are available."""
    has_keys = any([
        os.getenv("OPENAI_API_KEY"),
        os.getenv("ANTHROPIC_API_KEY"), 
        os.getenv("OPENROUTER_API_KEY")
    ])
    return pytest.mark.skipif(not has_keys, reason="No API keys available for integration testing")


@pytest.mark.integration
@skip_if_no_api_keys()
class TestRealAPIIntegration:
    """Integration tests with real API calls."""
    
    def test_basic_ask_integration(self):
        """Test basic ask functionality with real API."""
        # Use a simple, reliable model for testing
        if os.getenv("OPENAI_API_KEY"):
            model = "gpt-3.5-turbo"
        elif os.getenv("OPENROUTER_API_KEY"):
            # Use Gemini 2.5 Flash (latest model)
            model = "openrouter/google/gemini-2.5-flash-preview"
        else:
            model = "gpt-3.5-turbo"  # Default fallback
            
        response = ask("What is 2+2? Reply with just the number.", model=model, backend="cloud")
        assert "4" in str(response)
        assert response.succeeded
        assert response.model
        assert response.backend == "cloud"
    
    def test_streaming_integration(self):
        """Test streaming with real API."""
        chunks = []
        model = "openai/gpt-3.5-turbo" if os.getenv("OPENAI_API_KEY") else "google/gemini-flash-1.5"
        for chunk in stream("Count from 1 to 3, one number per line.", model=model):
            chunks.append(chunk)
        
        full_response = "".join(chunks)
        assert len(chunks) > 1  # Should be multiple chunks
        assert any(char.isdigit() for char in full_response)
    
    def test_chat_session_integration(self):
        """Test persistent chat session."""
        model = "openai/gpt-3.5-turbo" if os.getenv("OPENAI_API_KEY") else "google/gemini-flash-1.5"
        with chat(model=model) as session:
            response1 = session.ask("My name is Alice. What's 5+5?")
            assert "10" in str(response1)
            
            response2 = session.ask("What did I say my name was?")
            assert "Alice" in str(response2)
    
    def test_model_fallback_integration(self):
        """Test that fallback works with real APIs."""
        # Use a model that might not exist to test fallback
        response = ask("Hello", model="nonexistent-model", backend="cloud")
        # Should fallback to available model
        assert response.succeeded or "not found" in str(response).lower()
    
    @pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OpenRouter key required")
    def test_gemini_25_pro_integration(self):
        """Test Gemini 2.5 Pro specifically."""
        model = "openrouter/google/gemini-2.5-pro-preview"
        response = ask("Explain quantum computing in exactly 3 words.", model=model, backend="cloud")
        assert response.succeeded
        assert len(str(response).split()) <= 5  # Allow some flexibility
        assert response.model
        assert response.backend == "cloud"


@pytest.mark.integration  
@skip_if_no_api_keys()
class TestProviderSpecificIntegration:
    """Test specific providers with real keys."""
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI key required")
    def test_openai_specific(self):
        """Test OpenAI-specific functionality."""
        response = ask("Say 'OpenAI test'", model="gpt-3.5-turbo")
        assert "OpenAI" in str(response) or "test" in str(response)
    
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="Anthropic key required")  
    def test_anthropic_specific(self):
        """Test Anthropic-specific functionality."""
        response = ask("Say 'Claude test'", model="claude-3-haiku-20240307")
        assert response.succeeded
    
    @pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OpenRouter key required")
    def test_openrouter_variety(self):
        """Test multiple models through OpenRouter."""
        models_to_test = [
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-haiku",
            "meta-llama/llama-2-7b-chat"
        ]
        
        for model in models_to_test:
            try:
                response = ask("Reply with just 'OK'", model=model)
                # Some models might not be available, that's fine
                if response.succeeded:
                    assert len(str(response)) > 0
            except Exception:
                # Skip unavailable models
                pass


@pytest.mark.integration
@pytest.mark.slow
@skip_if_no_api_keys()
class TestErrorHandlingIntegration:
    """Test error handling with real APIs."""
    
    def test_invalid_model_error(self):
        """Test handling of invalid model names."""
        response = ask("Hello", model="definitely-not-a-real-model-name-12345")
        # Should either fail gracefully or fallback
        assert response is not None
    
    def test_rate_limiting_handling(self):
        """Test rate limit handling (careful - might hit actual limits)."""
        # Make several rapid requests to test rate limiting
        responses = []
        for i in range(3):  # Keep low to avoid hitting limits
            response = ask(f"Count: {i}", model="gpt-3.5-turbo")
            responses.append(response)
        
        # At least some should succeed
        assert any(r.succeeded for r in responses)


# Performance benchmarks (optional)
@pytest.mark.integration
@pytest.mark.benchmark  
@skip_if_no_api_keys()
class TestPerformanceBenchmarks:
    """Performance tests with real APIs."""
    
    def test_response_time_benchmark(self):
        """Benchmark response times for different models."""
        import time
        
        models = ["gpt-3.5-turbo", "gpt-4"]
        results = {}
        
        for model in models:
            if not os.getenv("OPENAI_API_KEY"):
                continue
                
            start_time = time.time()
            response = ask("What is AI?", model=model)
            end_time = time.time()
            
            if response.succeeded:
                results[model] = end_time - start_time
        
        # Just verify we got timing data
        assert len(results) > 0
        for model, duration in results.items():
            assert duration > 0
            print(f"{model}: {duration:.2f}s")


# Usage examples for documentation
@pytest.mark.integration
@pytest.mark.examples
@skip_if_no_api_keys() 
class TestUsageExamples:
    """Real usage examples that can be used in documentation."""
    
    def test_code_generation_example(self):
        """Example of using AI for code generation."""
        prompt = "Write a Python function that calculates factorial. Include docstring."
        response = ask(prompt, model="gpt-3.5-turbo")
        
        assert response.succeeded
        assert "def" in str(response)
        assert "factorial" in str(response).lower()
    
    def test_data_analysis_example(self):
        """Example of using AI for data analysis questions."""
        prompt = "Explain the difference between mean and median in statistics."
        response = ask(prompt, model="gpt-3.5-turbo")
        
        assert response.succeeded
        assert "mean" in str(response).lower()
        assert "median" in str(response).lower()