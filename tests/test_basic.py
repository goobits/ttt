#!/usr/bin/env python3
"""
Basic tests for Agents.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import ai, chat, stream, AgentResponse, ModelConfiguration, ModelInfo, ModelRouter, get_default_configuration


def test_response_object():
    """Test the AgentResponse object behaves like a string."""
    print("Testing AgentResponse object...")
    
    response = AgentResponse(
        content="Hello world",
        model="test-model",
        time=0.5,
        metadata={"tokens": 10}
    )
    
    # String-like behavior
    assert str(response) == "Hello world"
    assert len(response) == 11
    assert "world" in response
    assert response[0:5] == "Hello"
    assert bool(response) is True
    
    # Metadata access
    assert response.model == "test-model"
    assert response.time == 0.5
    assert response.tokens == 10
    
    print("✅ AgentResponse tests passed")


def test_model_routing():
    """Test the smart model routing."""
    print("\nTesting model routing...")
    
    router = ModelRouter()
    
    # Math queries
    math_model = router.route("Calculate 2 + 2")
    assert "gemini" in math_model.name.lower(), f"Expected Gemini for math, got {math_model.name}"
    
    # Code queries  
    code_model = router.route("Debug this Python code")
    assert "claude" in code_model.name.lower(), f"Expected Claude for code, got {code_model.name}"
    
    # Quick queries
    quick_model = router.route("What is CPU?")
    assert quick_model.speed == "fast", f"Expected fast model for quick query"
    
    print("✅ Model routing tests passed")


def test_chat_context():
    """Test the chat context manager."""
    print("\nTesting chat context...")
    
    # Get configuration and add mock model
    config = get_default_configuration()
    config.add_model(ModelInfo(
        name="mock",
        provider="mock",
        provider_name="mock",
        speed="fast"
    ))
    
    with chat(model="mock") as c:
        # Test that history is maintained
        c("Hello")
        c("How are you?")
        
        assert len(c.history) == 4  # 2 user + 2 assistant
        assert c.history[0]["role"] == "user"
        assert c.history[0]["content"] == "Hello"
        
    print("✅ Chat context tests passed")


def test_mock_backend():
    """Test that mock backend works."""
    print("\nTesting mock backend...")
    
    # Get configuration and ensure mock model exists
    config = get_default_configuration()
    config.add_model(ModelInfo(
        name="mock",
        provider="mock",
        provider_name="mock"
    ))
    
    # Test basic query
    response = ai("Hello", model="mock")
    assert response.model == "mock"
    assert not response.failed
    
    print("✅ Mock backend tests passed")


def run_all_tests():
    """Run all basic tests."""
    print("🧪 Running Agents.py Basic Tests\n")
    
    test_response_object()
    test_model_routing()
    test_chat_context()
    test_mock_backend()
    
    print("\n✨ All tests passed!")


if __name__ == "__main__":
    run_all_tests()