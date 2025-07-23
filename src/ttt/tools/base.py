"""Base classes for the tool system."""

import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ToolParameterType(str, Enum):
    """Supported parameter types for tools."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """Represents a single tool parameter."""

    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None


@dataclass
class ToolDefinition:
    """Defines a tool that can be called by the AI."""

    name: str
    description: str
    parameters: List[ToolParameter]
    function: Callable
    category: str = "general"

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling schema."""
        properties: Dict[str, Any] = {}
        required: List[str] = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type.value,
                "description": param.description,
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def to_anthropic_schema(self) -> Dict[str, Any]:
        """Convert to Anthropic function calling schema."""
        input_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        for param in self.parameters:
            input_schema["properties"][param.name] = {
                "type": param.type.value,
                "description": param.description,
            }
            if param.enum:
                input_schema["properties"][param.name]["enum"] = param.enum
            if param.required:
                input_schema["required"].append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": input_schema,
        }


@dataclass
class ToolCall:
    """Represents a call to a tool by the AI."""

    id: str
    name: str
    arguments: Dict[str, Any]
    result: Any = None
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        """Check if the tool call succeeded."""
        return self.error is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
            "result": self.result,
            "error": self.error,
            "succeeded": self.succeeded,
        }


@dataclass
class ToolResult:
    """Result of executing one or more tools."""

    calls: List[ToolCall] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        """Check if all tool calls succeeded."""
        return all(call.succeeded for call in self.calls)

    @property
    def failed_calls(self) -> List[ToolCall]:
        """Get list of failed tool calls."""
        return [call for call in self.calls if not call.succeeded]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "calls": [call.to_dict() for call in self.calls],
            "succeeded": self.succeeded,
            "failed_count": len(self.failed_calls),
        }


def extract_parameter_info(func: Callable) -> List[ToolParameter]:
    """Extract parameter information from a function using type hints and docstring."""
    sig = inspect.signature(func)
    parameters = []

    # Parse docstring for parameter descriptions
    doc_params = {}
    if func.__doc__:
        lines = func.__doc__.strip().split("\n")
        in_params = False
        for line in lines:
            line = line.strip()
            if line.lower().startswith("args:") or line.lower().startswith(
                "parameters:"
            ):
                in_params = True
                continue
            if in_params and line.startswith("returns:"):
                break
            if in_params and ":" in line:
                parts = line.split(":", 1)
                param_name = parts[0].strip()
                param_desc = parts[1].strip()
                doc_params[param_name] = param_desc

    for param_name, param in sig.parameters.items():
        # Skip self parameter
        if param_name == "self":
            continue

        # Determine type
        param_type = ToolParameterType.STRING  # default
        if param.annotation != inspect.Parameter.empty:
            if param.annotation is int:
                param_type = ToolParameterType.INTEGER
            elif param.annotation is float:
                param_type = ToolParameterType.NUMBER
            elif param.annotation is bool:
                param_type = ToolParameterType.BOOLEAN
            elif hasattr(param.annotation, "__origin__"):
                if param.annotation.__origin__ is list:
                    param_type = ToolParameterType.ARRAY
                elif param.annotation.__origin__ is dict:
                    param_type = ToolParameterType.OBJECT

        # Determine if required
        required = param.default == inspect.Parameter.empty

        # Get description
        description = doc_params.get(param_name, f"Parameter {param_name}")

        parameters.append(
            ToolParameter(
                name=param_name,
                type=param_type,
                description=description,
                required=required,
                default=(
                    param.default if param.default != inspect.Parameter.empty else None
                ),
            )
        )

    return parameters


def create_tool_definition(
    func: Callable,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "general",
) -> ToolDefinition:
    """Create a ToolDefinition from a function."""
    tool_name = name or func.__name__
    tool_description = description or func.__doc__ or f"Tool: {tool_name}"

    # Extract first line of docstring as description if no description provided
    if not description and func.__doc__:
        tool_description = func.__doc__.strip().split("\n")[0]

    parameters = extract_parameter_info(func)

    return ToolDefinition(
        name=tool_name,
        description=tool_description,
        parameters=parameters,
        function=func,
        category=category,
    )
