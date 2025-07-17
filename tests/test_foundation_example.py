"""Foundation example showing recommended testing patterns for the AI library."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

# Example 1: Testing the calculate tool with edge cases
from ai.tools.builtins import calculate


class TestCalculateToolFoundation:
    """Foundation example for testing tools with comprehensive edge cases."""

    def test_calculate_valid_expressions(self):
        """Test valid mathematical expressions."""
        test_cases = [
            ("2 + 2", "4"),
            ("10 - 3", "7"),
            ("3 * 4", "12"),
            ("15 / 3", "5"),
            ("2 ** 3", "8"),
            ("sqrt(16)", "4"),
            ("abs(-5)", "5"),
        ]
        
        for expression, expected in test_cases:
            result = calculate(expression)
            assert f"Result: {expected}" in result

    def test_calculate_edge_cases(self):
        """Test edge cases and error conditions."""
        # Division by zero
        result = calculate("1 / 0")
        assert "Error: Division by zero" in result
        
        # Invalid syntax
        result = calculate("2 +")
        assert "Error" in result
        
        # Empty expression
        result = calculate("")
        assert "Error" in result
        
        # Unsafe operations (should be blocked)
        result = calculate("__import__('os')")
        assert "Error" in result

    def test_calculate_complex_expressions(self):
        """Test complex mathematical expressions."""
        result = calculate("(2 + 3) * 4 - sqrt(16)")
        assert "Result: 16" in result
        
        result = calculate("sin(pi/2)")
        assert "Result: 1" in result


# Example 2: Testing LocalBackend with mocked HTTP client
from ai.backends.local import LocalBackend


class TestLocalBackendFoundation:
    """Foundation example for testing backends with proper mocking."""

    @pytest.fixture
    def backend(self):
        """Create a test backend instance."""
        return LocalBackend({
            "base_url": "http://localhost:11434",
            "default_model": "test-model"
        })

    @pytest.mark.asyncio
    async def test_ask_success_mocked(self, backend):
        """Test successful ask request with mocked httpx.AsyncClient."""
        # Mock response data
        mock_response_data = {
            "response": "Hello, world!",
            "eval_count": 25,
            "prompt_eval_count": 10,
            "eval_duration": 1000000000,  # 1 second in nanoseconds
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            # Create mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()

            # Set up the async context manager
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Make the request
            response = await backend.ask("Hello, AI!", model="test-model")

            # Verify response
            assert str(response) == "Hello, world!"
            assert response.model == "test-model"
            assert response.backend == "local"
            assert response.tokens_in == 10
            assert response.tokens_out == 25
            assert response.time_taken > 0

            # Verify the HTTP call was made correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:11434/api/generate"
            
            request_data = call_args[1]["json"]
            assert request_data["prompt"] == "Hello, AI!"
            assert request_data["model"] == "test-model"

    @pytest.mark.asyncio
    async def test_ask_http_error(self, backend):
        """Test ask with HTTP error response."""
        with patch("httpx.AsyncClient") as mock_client_class:
            # Set up HTTP error
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Model not found"
            
            http_error = httpx.HTTPStatusError(
                "404 Not Found",
                request=Mock(),
                response=mock_response
            )
            mock_client.post = AsyncMock(side_effect=http_error)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Should raise our custom exception
            from ai.exceptions import ModelNotFoundError
            with pytest.raises(ModelNotFoundError) as exc_info:
                await backend.ask("Test prompt", model="test-model")

            assert exc_info.value.details["model"] == "test-model"
            assert exc_info.value.details["backend"] == "local"


# Example 3: Testing CLI with Click's CliRunner
from click.testing import CliRunner
from ai.cli import main


class TestCLIFoundation:
    """Foundation example for testing CLI with Click's CliRunner."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_backend_status_command(self):
        """Test status command invocation."""
        with patch('ai.cli.show_backend_status') as mock_status:
            result = self.runner.invoke(main, ["--status"])
            
            assert result.exit_code == 0
            mock_status.assert_called_once()

    def test_ask_command_argument_parsing(self):
        """Test direct prompt parses arguments correctly."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_response.model = "gpt-4"
            mock_response.backend = "cloud"
            mock_response.time = 1.23
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, [
                "What is Python?",
                "--model", "gpt-4",
                "--verbose"
            ])
            
            assert result.exit_code == 0
            mock_ask.assert_called_once()
            
            # Check parsed arguments
            call_args = mock_ask.call_args
            assert call_args[0][0] == "What is Python?"
            call_kwargs = call_args[1]
            assert call_kwargs["model"] == "gpt-4"

    def test_help_output(self):
        """Test help output contains expected information."""
        result = self.runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        assert "TTT - Text-to-Text Processing Library" in result.stdout
        assert "--chat" in result.stdout
        assert "--status" in result.stdout
        assert "--models" in result.stdout

    def test_invalid_command_handling(self):
        """Test handling of invalid commands."""
        result = self.runner.invoke(main, ["nonexistent-command"])
        
        assert result.exit_code != 0
        # Click automatically handles unknown commands

    def test_missing_argument_handling(self):
        """Test handling of missing required arguments."""
        result = self.runner.invoke(main, ["ask"])  # Missing prompt
        
        assert result.exit_code != 0
        # Click puts error messages in output
        assert "Missing argument" in result.output or "Error" in result.output


# Async test example
class TestAsyncFoundation:
    """Foundation example for async testing patterns."""

    @pytest.mark.asyncio
    async def test_async_function_example(self):
        """Example of testing async functions."""
        from ai.api import ask_async
        
        with patch('ai.routing.router.smart_route') as mock_route:
            # Mock backend and response
            mock_backend = AsyncMock()
            mock_response = Mock()
            mock_response.__str__ = lambda x: "Test response"
            mock_backend.ask = AsyncMock(return_value=mock_response)
            
            mock_route.return_value = (mock_backend, "test-model")
            
            # Test the async function
            result = await ask_async("Test prompt")
            
            assert str(result) == "Test response"
            mock_backend.ask.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])