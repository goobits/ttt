"""Tool execution engine for running tool calls safely."""

import asyncio
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List
import json

from .base import ToolDefinition, ToolCall, ToolResult
from ..utils import get_logger

logger = get_logger(__name__)


class ToolExecutor:
    """Executes tool calls safely with proper error handling."""

    def __init__(self, max_workers: int = 4, timeout: float = 30.0):
        self.max_workers = max_workers
        self.timeout = timeout
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def execute_tool_call(
        self, tool_def: ToolDefinition, call_id: str, arguments: Dict[str, Any]
    ) -> ToolCall:
        """Execute a single tool call synchronously."""
        tool_call = ToolCall(id=call_id, name=tool_def.name, arguments=arguments)

        try:
            logger.debug(f"Executing tool {tool_def.name} with args: {arguments}")

            # Validate arguments against tool definition
            self._validate_arguments(tool_def, arguments)

            # Execute the function
            result = tool_def.function(**arguments)
            tool_call.result = result

            logger.debug(f"Tool {tool_def.name} completed successfully")

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            tool_call.error = error_msg
            logger.error(f"Tool {tool_def.name} failed: {error_msg}")
            logger.debug(traceback.format_exc())

        return tool_call

    async def execute_tool_call_async(
        self, tool_def: ToolDefinition, call_id: str, arguments: Dict[str, Any]
    ) -> ToolCall:
        """Execute a single tool call asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self.execute_tool_call, tool_def, call_id, arguments
        )

    def execute_multiple(
        self,
        tool_calls: List[Dict[str, Any]],
        tool_definitions: Dict[str, ToolDefinition],
    ) -> ToolResult:
        """Execute multiple tool calls synchronously."""
        results = []

        for call_data in tool_calls:
            call_id = call_data.get("id", str(uuid.uuid4()))
            tool_name = call_data["name"]
            arguments = call_data.get("arguments", {})

            if tool_name not in tool_definitions:
                error_call = ToolCall(
                    id=call_id,
                    name=tool_name,
                    arguments=arguments,
                    error=f"Tool '{tool_name}' not found",
                )
                results.append(error_call)
                continue

            tool_def = tool_definitions[tool_name]
            result = self.execute_tool_call(tool_def, call_id, arguments)
            results.append(result)

        return ToolResult(calls=results)

    async def execute_multiple_async(
        self,
        tool_calls: List[Dict[str, Any]],
        tool_definitions: Dict[str, ToolDefinition],
    ) -> ToolResult:
        """Execute multiple tool calls asynchronously."""
        tasks = []

        for call_data in tool_calls:
            call_id = call_data.get("id", str(uuid.uuid4()))
            tool_name = call_data["name"]
            arguments = call_data.get("arguments", {})

            if tool_name not in tool_definitions:
                # Create error result directly for missing tools
                error_call = ToolCall(
                    id=call_id,
                    name=tool_name,
                    arguments=arguments,
                    error=f"Tool '{tool_name}' not found",
                )
                tasks.append(asyncio.create_task(self._create_error_result(error_call)))
                continue

            tool_def = tool_definitions[tool_name]
            task = asyncio.create_task(
                self.execute_tool_call_async(tool_def, call_id, arguments)
            )
            tasks.append(task)

        # Execute all tasks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Tool execution timed out after {self.timeout}s")
            # Create timeout error results
            results = []
            for i, call_data in enumerate(tool_calls):
                call_id = call_data.get("id", str(uuid.uuid4()))
                error_call = ToolCall(
                    id=call_id,
                    name=call_data["name"],
                    arguments=call_data.get("arguments", {}),
                    error=f"Tool execution timed out after {self.timeout}s",
                )
                results.append(error_call)

        # Handle any exceptions
        tool_calls_list = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                call_data = tool_calls[i]
                call_id = call_data.get("id", str(uuid.uuid4()))
                error_call = ToolCall(
                    id=call_id,
                    name=call_data["name"],
                    arguments=call_data.get("arguments", {}),
                    error=f"Async execution error: {str(result)}",
                )
                tool_calls_list.append(error_call)
            else:
                tool_calls_list.append(result)

        return ToolResult(calls=tool_calls_list)

    async def _create_error_result(self, error_call: ToolCall) -> ToolCall:
        """Helper to create an error result asynchronously."""
        return error_call

    def _validate_arguments(
        self, tool_def: ToolDefinition, arguments: Dict[str, Any]
    ) -> None:
        """Validate arguments against tool definition."""
        # Check required parameters
        for param in tool_def.parameters:
            if param.required and param.name not in arguments:
                raise ValueError(f"Missing required parameter: {param.name}")

        # Check for unknown parameters
        param_names = {param.name for param in tool_def.parameters}
        for arg_name in arguments:
            if arg_name not in param_names:
                logger.warning(
                    f"Unknown parameter '{arg_name}' for tool '{tool_def.name}'"
                )

        # Basic type validation (could be enhanced)
        for param in tool_def.parameters:
            if param.name in arguments:
                value = arguments[param.name]
                if not self._validate_parameter_type(value, param.type.value):
                    logger.warning(
                        f"Parameter '{param.name}' type mismatch. "
                        f"Expected {param.type.value}, got {type(value).__name__}"
                    )

    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Basic type validation."""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            return isinstance(value, int)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        else:
            return True  # Unknown type, allow it

    def shutdown(self):
        """Shutdown the executor."""
        self._executor.shutdown(wait=True)


# Global executor instance
_global_executor = ToolExecutor()


def execute_tool_call(
    tool_def: ToolDefinition, call_id: str, arguments: Dict[str, Any]
) -> ToolCall:
    """Execute a single tool call using the global executor."""
    return _global_executor.execute_tool_call(tool_def, call_id, arguments)


async def execute_tool_call_async(
    tool_def: ToolDefinition, call_id: str, arguments: Dict[str, Any]
) -> ToolCall:
    """Execute a single tool call asynchronously using the global executor."""
    return await _global_executor.execute_tool_call_async(tool_def, call_id, arguments)


def execute_multiple(
    tool_calls: List[Dict[str, Any]], tool_definitions: Dict[str, ToolDefinition]
) -> ToolResult:
    """Execute multiple tool calls using the global executor."""
    return _global_executor.execute_multiple(tool_calls, tool_definitions)


async def execute_multiple_async(
    tool_calls: List[Dict[str, Any]], tool_definitions: Dict[str, ToolDefinition]
) -> ToolResult:
    """Execute multiple tool calls asynchronously using the global executor."""
    return await _global_executor.execute_multiple_async(tool_calls, tool_definitions)


def get_executor() -> ToolExecutor:
    """Get the global executor instance."""
    return _global_executor
