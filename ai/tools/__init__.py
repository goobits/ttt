"""Tool system for the AI library.

This module provides the @tool decorator and core functionality for adding
function calling capabilities to AI interactions.

Example usage:
    @tool
    def get_weather(city: str, units: str = "fahrenheit") -> str:
        '''Get weather information for a city.

        Args:
            city: Name of the city
            units: Temperature units (fahrenheit or celsius)
        '''
        return f"Weather in {city}: 72°{units[0].upper()}"

    # Use the tool
    response = ask("What's the weather in NYC?", tools=[get_weather])
"""

from typing import Callable, Optional, Union, List, Dict, Any
from functools import wraps

from .base import (
    ToolDefinition,
    ToolCall,
    ToolResult,
    ToolParameter,
    ToolParameterType,
    create_tool_definition,
)
from .registry import (
    ToolRegistry,
    register_tool,
    unregister_tool,
    get_tool,
    list_tools,
    get_categories,
    resolve_tools,
    clear_registry,
    get_registry,
)
from .executor import (
    ToolExecutor,
    ExecutionConfig,
    execute_tool,
    execute_tools,
    get_execution_stats,
)


def tool(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "general",
    register: bool = True
) -> Union[Callable, ToolDefinition]:
    """
    Decorator to mark a function as a tool.

    Can be used with or without parameters:

    @tool
    def simple_tool(arg: str) -> str:
        return f"Result: {arg}"

    @tool(name="custom_name", description="Custom description")
    def complex_tool(arg: str) -> str:
        return f"Result: {arg}"

    Args:
        func: The function to decorate (when used without parentheses)
        name: Custom name for the tool (defaults to function name)
        description: Custom description (defaults to function docstring)
        category: Category for organizing tools
        register: Whether to register in the global registry

    Returns:
        Either the decorated function (retains original behavior) or ToolDefinition
    """

    def decorator(f: Callable) -> Callable:
        # Create tool definition
        tool_def = create_tool_definition(f, name, description, category)

        # Register in global registry if requested
        if register:
            try:
                register_tool(f, name, description, category)
            except ValueError:
                # Tool already registered, that's okay
                pass

        # Add tool metadata to the function
        f._tool_definition = tool_def
        f._is_tool = True

        @wraps(f)
        def wrapper(*args, **kwargs):
            # Function still works normally
            return f(*args, **kwargs)

        # Preserve tool metadata on wrapper
        wrapper._tool_definition = tool_def
        wrapper._is_tool = True

        return wrapper

    if func is None:
        # Called with parameters: @tool(name="...", ...)
        return decorator
    else:
        # Called without parameters: @tool
        return decorator(func)


def is_tool(func: Callable) -> bool:
    """Check if a function is decorated as a tool."""
    return getattr(func, "_is_tool", False)


def get_tool_definition(func: Callable) -> Optional[ToolDefinition]:
    """Get the ToolDefinition for a decorated function."""
    return getattr(func, "_tool_definition", None)


# Compatibility wrapper functions for the old execution API
import asyncio
import uuid

_global_executor = None

def get_executor() -> ToolExecutor:
    """Get or create the global tool executor instance."""
    global _global_executor
    if _global_executor is None:
        _global_executor = ToolExecutor()
    return _global_executor


async def execute_tool_call_async(
    tool_def: ToolDefinition, call_id: str, arguments: Dict[str, Any]
) -> ToolCall:
    """Execute a single tool call asynchronously (compatibility wrapper)."""
    # First, try to register the tool if it's not already registered
    existing_tool = get_tool(tool_def.name)
    if not existing_tool:
        # Temporarily register the tool
        register_tool(tool_def.function, tool_def.name, tool_def.description, "test")
    
    try:
        # The new executor expects tool name, not definition
        result = await execute_tool(tool_def.name, arguments)
        # Update the result with the provided call_id
        result.id = call_id
        return result
    finally:
        # Clean up if we temporarily registered the tool
        if not existing_tool:
            try:
                unregister_tool(tool_def.name)
            except:
                pass


def execute_tool_call(
    tool_def: ToolDefinition, call_id: str, arguments: Dict[str, Any]
) -> ToolCall:
    """Execute a single tool call synchronously (compatibility wrapper)."""
    return asyncio.run(execute_tool_call_async(tool_def, call_id, arguments))


async def execute_multiple_async(
    tool_calls: List[Dict[str, Any]], tool_definitions: Dict[str, ToolDefinition]
) -> ToolResult:
    """Execute multiple tool calls asynchronously (compatibility wrapper)."""
    # Register any tools that aren't already in the registry
    temp_registered = []
    for tool_name, tool_def in tool_definitions.items():
        if not get_tool(tool_name):
            register_tool(tool_def.function, tool_name, tool_def.description, "test")
            temp_registered.append(tool_name)
    
    try:
        # Convert to the format expected by the new executor
        # The new executor's execute_tools expects a list of dicts with 'name' and 'arguments'
        # and doesn't need the tool definitions separately
        return await execute_tools(tool_calls, parallel=True)
    finally:
        # Clean up temporarily registered tools
        for tool_name in temp_registered:
            try:
                unregister_tool(tool_name)
            except:
                pass


def execute_multiple(
    tool_calls: List[Dict[str, Any]], tool_definitions: Dict[str, ToolDefinition]
) -> ToolResult:
    """Execute multiple tool calls synchronously (compatibility wrapper)."""
    return asyncio.run(execute_multiple_async(tool_calls, tool_definitions))


# Export all public classes and functions
__all__ = [
    # Decorator
    "tool",
    "is_tool",
    "get_tool_definition",
    # Base classes
    "ToolDefinition",
    "ToolCall",
    "ToolResult",
    "ToolParameter",
    "ToolParameterType",
    "create_tool_definition",
    # Registry functions
    "ToolRegistry",
    "register_tool",
    "unregister_tool",
    "get_tool",
    "list_tools",
    "get_categories",
    "resolve_tools",
    "clear_registry",
    "get_registry",
    # Execution functions
    "ToolExecutor",
    "ExecutionConfig",
    "execute_tool_call",
    "execute_tool_call_async",
    "execute_multiple",
    "execute_multiple_async",
    "get_executor",
    "execute_tool",
    "execute_tools",
    "get_execution_stats",
]
