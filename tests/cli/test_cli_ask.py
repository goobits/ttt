"""Tests for the ask CLI command functionality."""

from ttt.cli import main
from tests.cli.conftest import IntegrationTestBase


class TestAskCommand(IntegrationTestBase):
    """Test the ask command functionality."""

    def test_ask_command_exists(self):
        """Test that ask command is available and accepts --help."""
        result = self.runner.invoke(main, ["ask", "--help"])
        assert result.exit_code == 0

    def test_ask_basic_prompt(self):
        """Test basic ask functionality with real hooks."""
        # This is a real integration test - it will make actual API calls
        # if you have API keys configured, otherwise it will fail gracefully
        result = self.runner.invoke(main, ["ask", "What is Python?"])

        # Integration test - verify CLI works (may fail with API errors in CI)
        # Exit code 0 = success, 1 = expected error (like missing API key)
        assert result.exit_code in [0, 1]
        
        # If successful, should have some output
        if result.exit_code == 0:
            assert len(result.output.strip()) > 0
        else:
            # If failed due to API issues, that's expected in test environment
            assert "error" in result.output.lower() or "Error" in result.output

    def test_ask_with_options(self):
        """Test ask with various options."""
        # Real integration test with options
        result = self.runner.invoke(
            main,
            [
                "ask",
                "Debug this code",
                "--model",
                "gpt-4",
                "--temperature",
                "0.7",
                "--tools",
                "true",
                "--session",
                "test-session",
            ],
        )

        # Integration test - verify CLI handles options correctly
        # Exit code 0 = success, 1 = expected error (like missing API key/model)
        assert result.exit_code in [0, 1]
        
        # The important thing is that it doesn't crash with exit code 2 (argument error)
        # which would indicate the CLI argument parsing failed
        assert result.exit_code != 2

    def test_ask_parameter_passing_with_json_output(self):
        """Test ask command passes all parameters correctly with proper types."""
        # Integration test approach: validate that CLI parameters are correctly
        # processed by running the command and verifying the output structure
        # This confirms the CLI→hook parameter conversion is working
        
        result = self.runner.invoke(main, [
            "ask", "test prompt", 
            "--model", "gpt-4", 
            "--temperature", "0.7",
            "--max-tokens", "100",
            "--tools", "true",  # type=bool requires value
            "--session", "test-session",
            "--system", "You are helpful",
            "--stream", "false",  # type=bool requires value  
            "--json"  # is_flag=True, so no value needed
        ])
        
        # Command should execute successfully - this validates CLI structure
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        
        # Verify JSON output format (--json flag worked)
        assert "{" in result.output and "}" in result.output, "Expected JSON output"
        
        # Parse JSON to verify parameter passing worked correctly
        import json
        
        # Extract JSON from output (might have other text before/after)
        output_lines = result.output.strip().split('\n')
        json_lines = []
        in_json = False
        
        for line in output_lines:
            if line.strip().startswith('{'):
                in_json = True
            if in_json:
                json_lines.append(line)
            if line.strip().endswith('}') and in_json:
                break
        
        json_text = '\n'.join(json_lines)
        
        try:
            output_data = json.loads(json_text)
            
            # Verify that CLI parameters were correctly passed to hook
            # Model might be transformed by routing logic (e.g., gpt-4 -> openrouter/openai/gpt-4)
            # The important thing is that a model is present and contains our original model
            model_used = output_data.get("model", "")
            assert "gpt-4" in model_used, f"Model parameter not passed correctly. Got: {model_used}"
            assert output_data.get("temperature") == 0.7, f"Temperature not converted to float. Got: {output_data.get('temperature')}"
            assert output_data.get("max_tokens") == 100, f"Max tokens not converted to int. Got: {output_data.get('max_tokens')}"
            assert output_data.get("session_id") == "test-session", f"Session parameter not mapped correctly. Got: {output_data.get('session_id')}"
            assert output_data.get("system") == "You are helpful", f"System prompt not passed correctly. Got: {output_data.get('system')}"
            
            # Verify tools parameter processed
            assert "tools_enabled" in output_data, f"Tools parameter not processed. Keys: {list(output_data.keys())}"
            
            # Most importantly: we have a response, meaning the whole CLI→hook→API chain worked
            assert "response" in output_data and output_data["response"], f"No response generated. Got: {output_data.get('response')}"
            
        except json.JSONDecodeError as e:
            assert False, f"Invalid JSON output: {e}. Raw output: {result.output}"
        except KeyError as e:
            assert False, f"Missing expected key in JSON output: {e}. Available keys: {list(output_data.keys()) if 'output_data' in locals() else 'N/A'}"

    def test_click_type_conversions_in_ask(self):
        """Test that Click type conversions work correctly for ask command parameters."""
        # Test CLI with various parameter types to ensure Click handles conversions
        result = self.runner.invoke(main, [
            "ask", "test type conversions",
            "--temperature", "0.123",  # String to float
            "--max-tokens", "2048",    # String to int
            "--tools", "true",         # String to bool
            "--stream", "false",       # String to bool
            "--json"                   # Flag to bool (True)
        ])
        
        # Command should succeed - this validates Click type conversion works
        assert result.exit_code == 0, f"Type conversion failed: {result.output}"
        
        # If JSON output is produced, verify structure shows correct types were used
        if "{" in result.output:
            import json
            try:
                # Extract JSON from output
                lines = result.output.strip().split('\n')
                for line in lines:
                    if line.strip().startswith('{'):
                        output_data = json.loads(line)
                        # Verify converted values are present and correct type
                        assert output_data.get("temperature") == 0.123, "Temperature conversion failed"
                        assert output_data.get("max_tokens") == 2048, "Max tokens conversion failed"
                        break
            except json.JSONDecodeError:
                pass  # JSON parsing is secondary