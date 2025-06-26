#!/usr/bin/env python3
"""
Example of using tools with chat sessions.

This demonstrates how to:
- Create chat sessions with tools
- Use persistent sessions with tools
- Save and load sessions with tool history
"""

from ai import chat
from ai.chat import PersistentChatSession
from ai.tools import tool


# Define some example tools
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The city name to get weather for
    """
    # In a real implementation, this would call a weather API
    weather_data = {
        "New York": "72°F, Sunny",
        "London": "60°F, Cloudy",
        "Tokyo": "68°F, Clear",
        "Sydney": "75°F, Partly Cloudy",
    }
    return weather_data.get(city, f"Unknown weather for {city}")


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate
    """
    try:
        # Note: eval() is dangerous in production! Use a proper math parser
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def basic_chat_with_tools():
    """Basic example of chat session with tools."""
    print("=== Basic Chat with Tools ===")

    # Create a chat session with tools
    with chat(tools=[get_weather, calculate]) as session:
        # Ask about weather
        response = session.ask("What's the weather in New York?")
        print(f"User: What's the weather in New York?")
        print(f"Assistant: {response}")

        # Ask for calculation
        response = session.ask("Calculate 15 * 23 + 42")
        print(f"\nUser: Calculate 15 * 23 + 42")
        print(f"Assistant: {response}")


def persistent_chat_with_tools():
    """Example of persistent chat session with tools."""
    print("\n=== Persistent Chat with Tools ===")

    # Create persistent session with tools
    session = PersistentChatSession(
        system="You are a helpful assistant with access to weather and calculation tools.",
        tools=[get_weather, calculate],
    )

    # First conversation
    print(f"Session ID: {session.session_id}")
    response = session.ask("What's the weather in London?")
    print(f"User: What's the weather in London?")
    print(f"Assistant: {response}")

    # Save session
    save_path = "weather_chat.json"
    session.save(save_path)
    print(f"\nSession saved to {save_path}")

    # Load session and continue
    loaded_session = PersistentChatSession.load(save_path)
    print(f"\nLoaded session with {len(loaded_session.history)} messages")

    # Continue conversation
    response = loaded_session.ask("What about Tokyo?")
    print(f"User: What about Tokyo?")
    print(f"Assistant: {response}")

    # Show tool usage statistics
    print(f"\nTool usage statistics:")
    for tool_name, count in loaded_session.metadata.get("tools_used", {}).items():
        print(f"  - {tool_name}: {count} calls")


def cli_tool_examples():
    """Show CLI examples with tools."""
    print("\n=== CLI Tool Examples ===")
    print("You can use tools from the command line:")
    print()
    print("1. Using registered tools:")
    print('   ai "What\'s the weather?" --tools "get_weather"')
    print()
    print("2. Using module functions:")
    print('   ai "Calculate this" --tools "math:sqrt,math:pow"')
    print()
    print("3. Using custom script functions:")
    print('   ai "Process data" --tools "/path/to/tools.py:process_data"')
    print()
    print("4. Multiple tools:")
    print('   ai "Complex task" --tools "tool1,module:tool2,/script.py:tool3"')


def main():
    """Run all examples."""
    # Mock backend for examples
    import os

    os.environ["AI_MOCK_BACKEND"] = "true"

    try:
        basic_chat_with_tools()
        persistent_chat_with_tools()
        cli_tool_examples()
    except Exception as e:
        print(f"\nNote: Examples require a working AI backend.")
        print(f"Error: {e}")
        print("\nShowing CLI examples instead:")
        cli_tool_examples()


if __name__ == "__main__":
    main()
