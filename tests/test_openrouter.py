#!/usr/bin/env python3
"""
Test Agents.py with OpenRouter models only
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure LiteLLM for OpenRouter
os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")

# Import after setting env vars
from agents import ai, chat, stream

def main():
    print("🤖 Testing Agents.py with OpenRouter Models\n")
    
    # Test 1: Direct OpenRouter call
    print("1. Direct OpenRouter Gemini Flash:")
    response = ai("What is the capital of France?", model="openrouter/gemini-flash-1.5")
    print(f"Response: {response}")
    print(f"Model used: {response.model}")
    print(f"Time taken: {response.time:.2f}s\n")
    
    # Test 2: Math with OpenRouter
    print("2. Math calculation:")
    response = ai("Calculate 15% tip on $42.50", model="openrouter/gemini-flash-1.5")
    print(f"Response: {response}")
    print(f"Time taken: {response.time:.2f}s\n")
    
    # Test 3: Code analysis with OR alias
    print("3. Code analysis with alias:")
    code = '''def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)'''
    
    response = ai("Explain this code in one sentence", code=code, model="or-gemini-flash")
    print(f"Response: {response}")
    print(f"Model used: {response.model}\n")
    
    # Test 4: Conversation with OpenRouter
    print("4. Conversation with OpenRouter:")
    with chat(model="openrouter/gemini-flash-1.5", system="Be very brief") as assistant:
        response = assistant("What's Python?")
        print(f"Assistant: {response}")
        
        response = assistant("Name one use case")
        print(f"Assistant: {response}\n")
    
    # Test 5: Streaming with OpenRouter
    print("5. Streaming with OpenRouter:")
    print("Story: ", end="", flush=True)
    for chunk in stream("Tell me a 3-word story", model="openrouter/gemini-flash-1.5"):
        print(chunk, end="", flush=True)
    print("\n")
    
    # Test 6: Using different OpenRouter models
    print("6. Testing other OpenRouter models:")
    
    # Try GPT-4 via OpenRouter
    try:
        response = ai("What is 5+5?", model="openrouter/gpt-4")
        print(f"OpenRouter GPT-4: {response}")
    except Exception as e:
        print(f"OpenRouter GPT-4 error: {e}")
    
    # Try Claude via OpenRouter
    try:
        response = ai("What is 6+6?", model="openrouter/claude-3-sonnet")
        print(f"OpenRouter Claude: {response}")
    except Exception as e:
        print(f"OpenRouter Claude error: {e}")


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not found in .env file")
        sys.exit(1)
    
    main()