#!/usr/bin/env python3
"""
Test Agents.py with real AI calls using OpenRouter
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
    print("🤖 Testing Agents.py with Real AI (OpenRouter)\n")
    
    # Test 1: Simple query with OpenRouter model
    print("1. Testing OpenRouter Gemini Flash:")
    try:
        response = ai("What is 2+2?", model="openrouter/gemini-flash-1.5")
        print(f"Response: {response}")
        print(f"Model used: {response.model}")
        print(f"Time taken: {response.time:.2f}s\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Test 2: Let the router pick a math model
    print("2. Auto-routing for math:")
    try:
        response = ai("Calculate 15% tip on $42.50")
        print(f"Response: {response}")
        print(f"Model used: {response.model}")
        print(f"Time taken: {response.time:.2f}s\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Test 3: Code analysis
    print("3. Code analysis:")
    code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
    try:
        response = ai("What does this code do and what's its time complexity?", code=code)
        print(f"Response: {response[:200]}...")
        print(f"Model used: {response.model}")
        print(f"Time taken: {response.time:.2f}s\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Test 4: Quick conversation
    print("4. Conversation test:")
    try:
        with chat(system="You are a helpful assistant. Keep responses brief.") as assistant:
            response = assistant("What's the capital of France?")
            print(f"Assistant: {response}")
            
            response = assistant("What's its population?")
            print(f"Assistant: {response}")
            print(f"Model used: {response.model}\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Test 5: Streaming (if supported)
    print("5. Streaming test:")
    try:
        print("Response: ", end="", flush=True)
        for chunk in stream("Tell me a haiku about programming"):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\nError: {e}\n")


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not found in .env file")
        print("Please ensure .env file exists with your OpenRouter API key")
        sys.exit(1)
    
    main()