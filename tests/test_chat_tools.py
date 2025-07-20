"""Tests for tool support in chat sessions."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ttt.api import chat
from ttt.chat import PersistentChatSession
from ttt.chat import PersistentChatSession as ChatSession
from ttt.models import AIResponse
from ttt.tools import ToolCall, ToolResult


class TestChatSessionTools:
    """Test tool support in ChatSession."""

    def test_chat_session_with_tools(self):
        """Test creating ChatSession with tools."""

        def test_tool(x: int) -> int:
            return x * 2

        session = ChatSession(tools=[test_tool])
        assert session.tools == [test_tool]

    def test_chat_session_ask_with_tools(self):
        """Test ChatSession.ask passes tools to backend."""

        def test_tool(x: int) -> int:
            return x * 2

        with patch("ttt.routing.router.smart_route") as mock_route:
            backend_instance = Mock()
            backend_instance.ask = AsyncMock(
                return_value=AIResponse("Response", model="test", backend="test")
            )
            mock_route.return_value = (backend_instance, "test-model")

            session = ChatSession(tools=[test_tool])
            session.ask("Test prompt")

            # Verify tools were passed to backend
            backend_instance.ask.assert_called_once()
            call_args = backend_instance.ask.call_args
            assert call_args.kwargs.get("tools") == [test_tool]

    def test_chat_context_manager_with_tools(self):
        """Test chat context manager with tools."""

        def test_tool(x: int) -> int:
            return x * 2

        with chat(tools=[test_tool]) as session:
            assert session.tools == [test_tool]


class TestPersistentChatSessionTools:
    """Test tool support in PersistentChatSession."""

    def test_persistent_session_with_tools(self):
        """Test creating PersistentChatSession with tools."""

        def test_tool(x: int) -> int:
            return x * 2

        session = PersistentChatSession(tools=[test_tool])
        assert session.tools == [test_tool]
        assert "tools_used" in session.metadata

    def test_persistent_session_tracks_tool_usage(self):
        """Test that PersistentChatSession tracks tool usage in metadata."""

        def test_tool(x: int) -> int:
            return x * 2

        from ttt.chat import router

        with patch.object(router, "smart_route") as mock_smart_route:
            backend_instance = Mock()

            # Create response with tool calls
            tool_result = ToolResult(
                calls=[
                    ToolCall(
                        id="call_1",
                        name="test_tool",
                        arguments={"x": 5},
                        result=10,
                        error=None,
                    )
                ]
            )
            response = AIResponse(
                "Response with tool",
                model="test",
                backend="test",
                tool_result=tool_result,
            )

            backend_instance.ask = AsyncMock(return_value=response)
            mock_smart_route.return_value = (backend_instance, "test-model")

            session = PersistentChatSession(tools=[test_tool])
            session.ask("Use the tool")

            # Check tool usage was tracked
            assert "test_tool" in session.metadata["tools_used"]
            assert session.metadata["tools_used"]["test_tool"] == 1

            # Check tool call was saved in history
            assert session.history[-1]["tools_called"] is True
            assert len(session.history[-1]["tool_calls"]) == 1
            assert session.history[-1]["tool_calls"][0]["name"] == "test_tool"

    def test_persistent_session_save_load_tools(self, tmp_path):
        """Test saving and loading session with tools."""

        def test_tool(x: int) -> int:
            return x * 2

        # Create session with tools
        session = PersistentChatSession(tools=[test_tool], system="Test system")

        # Save session
        save_path = tmp_path / "test_session.json"
        session.save(save_path)

        # Load session
        loaded_session = PersistentChatSession.load(save_path)

        # Check tools were preserved (as names)
        assert loaded_session.tools is not None
        assert len(loaded_session.tools) == 1
        assert loaded_session.tools[0] == "test_tool"

    def test_tool_serialization(self):
        """Test tool serialization methods."""

        def test_function(x: int) -> int:
            return x * 2

        class MockToolDef:
            name = "mock_tool"
            description = "Mock tool"

        session = PersistentChatSession(
            tools=[test_function, MockToolDef(), "string_tool"]
        )

        serialized = session._serialize_tools()

        assert len(serialized) == 3
        assert serialized[0]["type"] == "function_name"
        assert serialized[0]["name"] == "test_function"
        assert serialized[1]["type"] == "tool_definition"
        assert serialized[1]["name"] == "mock_tool"
        assert serialized[2]["type"] == "tool_name"
        assert serialized[2]["name"] == "string_tool"

    def test_tool_deserialization(self):
        """Test tool deserialization methods."""
        serialized = [
            {"type": "function_name", "name": "test_function", "module": "test"},
            {"type": "tool_definition", "name": "mock_tool", "description": "Mock"},
            {"type": "tool_name", "name": "string_tool"},
        ]

        tools = PersistentChatSession._deserialize_tools(serialized)

        assert len(tools) == 3
        assert tools[0] == "test_function"
        assert tools[1] == "mock_tool"
        assert tools[2] == "string_tool"

    def test_persistent_chat_with_context_manager(self):
        """Test persistent chat with tools using context manager."""

        def test_tool(x: int) -> int:
            return x * 2

        with chat(persist=True, tools=[test_tool]) as session:
            assert isinstance(session, PersistentChatSession)
            assert session.tools == [test_tool]


class TestCLIToolSupport:
    """Test CLI tool support."""

    def test_cli_with_tools(self):
        """Test CLI argument parsing with --tools flag."""
        from click.testing import CliRunner

        from ttt.cli import main

        runner = CliRunner()

        with patch("ttt.ask") as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response

            with patch("ttt.cli.resolve_tools") as mock_resolve:
                mock_resolve.return_value = []  # Simplified for test

                result = runner.invoke(
                    main, ["ask", "Test prompt", "--tools", "math:add,string:upper"]
                )

                assert result.exit_code == 0
                # Verify tools were parsed and resolved
                mock_resolve.assert_called_once_with(["math:add", "string:upper"])

    def test_resolve_tools_from_registry(self):
        """Test resolving tools from registry."""
        from ttt.cli import resolve_tools
        from ttt.tools.registry import clear_registry, register_tool

        # Register a test tool
        def test_tool(x: int) -> int:
            return x * 2

        clear_registry()
        register_tool(test_tool)

        # Resolve by name
        tools = resolve_tools(["test_tool"])
        assert len(tools) == 1
        # resolve_tools returns functions, not ToolDefinition objects
        assert callable(tools[0])

        clear_registry()

    def test_resolve_tools_from_module(self):
        """Test resolving tools from module imports."""
        from ttt.cli import resolve_tools
        from ttt.tools import register_tool, tool, unregister_tool

        # Register a test tool in a test category
        @tool(register=False)
        def my_function(x):
            return x * 2

        register_tool(my_function, "my_function", "Test function", "mymodule")

        try:
            tools = resolve_tools(["mymodule:my_function"])
            assert len(tools) == 1
            assert callable(tools[0])  # Check it's callable
        finally:
            # Clean up
            try:
                unregister_tool("my_function")
            except Exception:
                pass  # Tool might not be registered

    def test_resolve_tools_handles_errors(self):
        """Test tool resolution handles errors gracefully."""
        from ttt.cli import resolve_tools

        # Non-existent module
        tools = resolve_tools(["nonexistent:function"])
        assert len(tools) == 0

        # Non-existent function in registry
        tools = resolve_tools(["nonexistent_tool"])
        assert len(tools) == 0


if __name__ == "__main__":
    pytest.main([__file__])
