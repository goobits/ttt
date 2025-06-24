#!/usr/bin/env python3
"""
Simple test with OpenRouter
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure LiteLLM for OpenRouter
os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")

# Test direct litellm usage first
print("Testing direct LiteLLM with OpenRouter...")
try:
    from litellm import completion
    
    response = completion(
        model="openrouter/google/gemini-flash-1.5",
        messages=[{"role": "user", "content": "What is 2+2? Reply with just the number."}],
        api_base="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"]
    )
    
    print(f"Direct LiteLLM response: {response.choices[0].message.content}")
    print("✅ Direct LiteLLM works!\n")
except Exception as e:
    print(f"❌ Direct LiteLLM error: {e}\n")

# Now test through agents
print("Testing through Agents.py...")
try:
    # Import agents after setting env vars
    from agents import ai
    
    response = ai("What is 3+3? Reply with just the number.", model="openrouter/gemini-flash-1.5")
    print(f"Agents.py response: {response}")
    print(f"Model used: {response.model}")
    print("✅ Agents.py works!")
except Exception as e:
    print(f"❌ Agents.py error: {e}")
    import traceback
    traceback.print_exc()