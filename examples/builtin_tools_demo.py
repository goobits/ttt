#!/usr/bin/env python3
"""
Demonstration of AI Library Built-in Tools

This example shows how to use the comprehensive set of built-in tools
that come with the AI library for common tasks.
"""

import asyncio
from ai import ask
from ai.tools import list_tools, get_tool
from ai.tools.builtins import (
    web_search,
    read_file,
    write_file,
    list_directory,
    calculate,
    get_current_time,
    http_request,
    run_python,
)


def demo_tool_discovery():
    """Show how to discover available tools."""
    print("=== Tool Discovery ===\n")

    # List all tools
    all_tools = list_tools()
    print(f"Total available tools: {len(all_tools)}")

    # Group by category
    categories = {}
    for tool in all_tools:
        if tool.category not in categories:
            categories[tool.category] = []
        categories[tool.category].append(tool.name)

    print("\nTools by category:")
    for category, tools in sorted(categories.items()):
        print(f"  {category}: {', '.join(tools)}")

    # Get specific tool info
    print("\n=== Tool Details ===")
    calc_tool = get_tool("calculate")
    if calc_tool:
        print(f"Name: {calc_tool.name}")
        print(f"Description: {calc_tool.description}")
        print(f"Parameters:")
        for param in calc_tool.parameters:
            print(f"  - {param.name} ({param.type.value}): {param.description}")


def demo_file_operations():
    """Demonstrate file operation tools."""
    print("\n=== File Operations Demo ===\n")

    # List current directory
    print("1. Listing Python files:")
    response = ask(
        "List all Python files in the current directory", tools=["list_directory"]
    )
    print(f"Response: {response.response}")

    # Create a test file
    print("\n2. Creating a test file:")
    response = ask(
        "Create a file called 'test_output.txt' with the content 'Hello from AI tools!'",
        tools=["write_file"],
    )
    print(f"Response: {response.response}")

    # Read the file back
    print("\n3. Reading the file:")
    response = ask("Read the contents of test_output.txt", tools=["read_file"])
    print(f"Response: {response.response}")


def demo_web_and_calculation():
    """Demonstrate web search and calculation tools."""
    print("\n=== Web Search & Calculation Demo ===\n")

    # Search and calculate
    response = ask(
        "Search for the distance from Earth to Mars in kilometers, "
        "then calculate how long it would take to travel there at 50,000 km/h",
        tools=["web_search", "calculate"],
    )
    print(f"Response: {response.response}")

    if response.tools_called:
        print("\nTools used:")
        for call in response.tool_calls:
            print(f"  - {call.name}: {'Success' if call.succeeded else 'Failed'}")


def demo_time_operations():
    """Demonstrate time-related tools."""
    print("\n=== Time Operations Demo ===\n")

    response = ask(
        "What time is it right now in Tokyo, London, and New York? "
        "Show me in 24-hour format.",
        tools=["get_current_time"],
    )
    print(f"Response: {response.response}")


def demo_code_execution():
    """Demonstrate safe code execution."""
    print("\n=== Code Execution Demo ===\n")

    response = ask(
        "Write and run a Python script that generates the first 10 Fibonacci numbers",
        tools=["run_python"],
    )
    print(f"Response: {response.response}")

    if response.tools_called:
        for call in response.tool_calls:
            if call.name == "run_python" and call.succeeded:
                print(f"\nCode output:\n{call.result}")


def demo_complex_workflow():
    """Demonstrate a complex multi-tool workflow."""
    print("\n=== Complex Workflow Demo ===\n")

    response = ask(
        "Search for information about Python list comprehensions, "
        "create a Python example that demonstrates them, "
        "save it to 'list_comp_demo.py', "
        "and then run it to show the output",
        tools=["web_search", "write_file", "run_python"],
    )

    print(f"Response: {response.response}")

    if response.tools_called:
        print("\nWorkflow steps:")
        for i, call in enumerate(response.tool_calls, 1):
            status = "✓" if call.succeeded else "✗"
            print(f"  {i}. {status} {call.name}")
            if not call.succeeded:
                print(f"     Error: {call.error}")


def demo_api_requests():
    """Demonstrate HTTP API requests."""
    print("\n=== API Request Demo ===\n")

    # Get public API data
    response = ask(
        "Make a request to https://api.github.com/users/python and tell me about the Python organization",
        tools=["http_request"],
    )
    print(f"Response: {response.response}")


def main():
    """Run all demonstrations."""
    print("Built-in Tools Demonstration")
    print("=" * 50)

    # Show available tools
    demo_tool_discovery()

    # Demonstrate each category
    demos = [
        demo_file_operations,
        demo_web_and_calculation,
        demo_time_operations,
        demo_code_execution,
        demo_api_requests,
        demo_complex_workflow,
    ]

    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\nError in {demo.__name__}: {e}")

    print("\n" + "=" * 50)
    print("Demonstration complete!")

    # Cleanup
    import os

    for file in ["test_output.txt", "list_comp_demo.py"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up: {file}")


if __name__ == "__main__":
    main()
