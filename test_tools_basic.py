#!/usr/bin/env python3
"""Basic test for tool functionality."""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from ai.tools import tool, ToolDefinition
from ai.tools.registry import register_tool, get_tool, list_tools


def test_tool_decorator():
    """Test the @tool decorator."""
    
    @tool
    def get_weather(city: str, units: str = "fahrenheit") -> str:
        """Get weather information for a city.
        
        Args:
            city: Name of the city
            units: Temperature units (fahrenheit or celsius)
        """
        return f"Weather in {city}: 72°{units[0].upper()}"
    
    # Test that the function still works normally
    result = get_weather("NYC")
    assert "Weather in NYC: 72°F" in result
    print("✅ Tool function works normally")
    
    # Test that it has tool metadata
    assert hasattr(get_weather, '_tool_definition')
    assert hasattr(get_weather, '_is_tool')
    assert get_weather._is_tool is True
    print("✅ Tool metadata attached")
    
    # Test tool definition
    tool_def = get_weather._tool_definition
    assert isinstance(tool_def, ToolDefinition)
    assert tool_def.name == "get_weather"
    assert "weather information" in tool_def.description.lower()
    assert len(tool_def.parameters) == 2  # city and units
    print("✅ Tool definition created correctly")
    
    # Test parameter extraction
    city_param = next(p for p in tool_def.parameters if p.name == "city")
    units_param = next(p for p in tool_def.parameters if p.name == "units")
    
    assert city_param.required is True
    assert units_param.required is False
    assert units_param.default == "fahrenheit"
    print("✅ Parameter metadata extracted correctly")
    
    return tool_def


def test_tool_schemas():
    """Test schema generation for different providers."""
    
    @tool
    def calculate(x: int, y: int, operation: str = "add") -> int:
        """Perform a calculation.
        
        Args:
            x: First number
            y: Second number
            operation: Operation to perform (add, subtract, multiply, divide)
        """
        if operation == "add":
            return x + y
        elif operation == "subtract":
            return x - y
        elif operation == "multiply":
            return x * y
        elif operation == "divide":
            return x // y if y != 0 else 0
        return 0
    
    tool_def = calculate._tool_definition
    
    # Test OpenAI schema
    openai_schema = tool_def.to_openai_schema()
    assert openai_schema["type"] == "function"
    assert openai_schema["function"]["name"] == "calculate"
    assert "calculation" in openai_schema["function"]["description"].lower()
    
    properties = openai_schema["function"]["parameters"]["properties"]
    assert "x" in properties
    assert "y" in properties
    assert "operation" in properties
    assert properties["x"]["type"] == "integer"
    assert properties["operation"]["type"] == "string"
    
    required = openai_schema["function"]["parameters"]["required"]
    assert "x" in required
    assert "y" in required
    assert "operation" not in required  # Has default value
    print("✅ OpenAI schema generation works")
    
    # Test Anthropic schema
    anthropic_schema = tool_def.to_anthropic_schema()
    assert anthropic_schema["name"] == "calculate"
    assert "calculation" in anthropic_schema["description"].lower()
    
    input_schema = anthropic_schema["input_schema"]
    assert input_schema["type"] == "object"
    assert "x" in input_schema["properties"]
    assert "y" in input_schema["properties"]
    assert "operation" in input_schema["properties"]
    print("✅ Anthropic schema generation works")


def test_tool_registry():
    """Test the tool registry functionality."""
    
    def manual_tool(message: str) -> str:
        """Send a message."""
        return f"Message: {message}"
    
    # Register manually
    tool_def = register_tool(manual_tool, description="Send a message to someone")
    assert tool_def.name == "manual_tool"
    print("✅ Manual tool registration works")
    
    # Retrieve from registry
    retrieved = get_tool("manual_tool")
    assert retrieved is not None
    assert retrieved.name == "manual_tool"
    print("✅ Tool retrieval from registry works")
    
    # List tools
    all_tools = list_tools()
    tool_names = [t.name for t in all_tools]
    assert "manual_tool" in tool_names
    assert "get_weather" in tool_names  # From previous test
    print("✅ Tool listing works")


if __name__ == "__main__":
    print("🧪 Testing basic tool functionality...")
    print()
    
    try:
        test_tool_decorator()
        print()
        
        test_tool_schemas()
        print()
        
        test_tool_registry()
        print()
        
        print("✅ All basic tool tests passed!")
        print()
        print("🎉 Tool system is working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)