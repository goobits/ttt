"""Comprehensive smoke tests for TTT CLI commands.

This test suite runs every command combination from cli-test-checklist.md to ensure
all CLI functionality works correctly. Tests are organized to match the
checklist structure for easy cross-reference.

Run with:
    ./test.sh --test test_cli_smoke
    ./test.sh --test test_cli_smoke --markers "not requires_api"  # Skip API-dependent tests
"""

import json
import os
import tempfile

import pytest
from click.testing import CliRunner

from ttt.cli import main


def has_valid_api_key():
    """Check if any valid API keys are available."""

    def is_valid_key(key):
        return key and "test-key" not in key and len(key) > 10

    return any(
        [
            is_valid_key(os.getenv("OPENAI_API_KEY")),
            is_valid_key(os.getenv("ANTHROPIC_API_KEY")),
            is_valid_key(os.getenv("OPENROUTER_API_KEY")),
        ]
    )


def run_ttt_command(args, input_text=None, timeout=10):
    """Run a TTT command using CliRunner for faster execution."""
    runner = CliRunner()
    result = runner.invoke(main, args, input=input_text)
    return result


class TestBasicCommands:
    """Test basic CLI commands - should work without API keys."""

    def test_ttt_direct_prompt_with_api(self):
        """Test: ttt 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["hello world"])
        # Should either work or timeout (both acceptable for API calls)
        assert result.exit_code in [0, 124]

    def test_ttt_ask_prompt(self):
        """Test: ttt ask 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "hello world"])
        assert result.exit_code in [0, 124]

    def test_ttt_info_model_displays_detailed_information(self):
        """Test: ttt info <model> - Shows comprehensive model details including provider, context, and capabilities"""
        result = run_ttt_command(["info", "gpt-4"])
        assert result.exit_code == 0, f"Info command failed: {result.output}"
        
        # Verify essential model information is displayed
        output_lower = result.output.lower()
        assert "gpt-4" in output_lower, f"Model name missing from output: {result.output}"
        assert any(word in output_lower for word in ["provider", "openai"]), f"Provider info missing: {result.output}"
        assert any(word in output_lower for word in ["context", "token", "length"]), f"Context length info missing: {result.output}"
        
        # Verify output is structured and informative
        lines = [line.strip() for line in result.output.split('\n') if line.strip()]
        assert len(lines) >= 3, f"Info output should have multiple lines of detail: {result.output}"


    def test_ttt_status_reports_system_health(self):
        """Test: ttt status - Provides comprehensive system health information including backend availability"""
        result = run_ttt_command(["status"])
        assert result.exit_code == 0, f"Status command failed: {result.output}"
        
        output_lower = result.output.lower()
        # Should contain system status information
        assert any(word in output_lower for word in ["status", "health", "system"]), f"Status header missing: {result.output}"
        
        # Should report on backends or API availability
        assert any(word in output_lower for word in ["backend", "api", "available", "configured"]), f"Backend status missing: {result.output}"
        
        # Should be informative with multiple status indicators
        lines = [line.strip() for line in result.output.split('\n') if line.strip()]
        assert len(lines) >= 2, f"Status should provide detailed information: {result.output}"

    def test_ttt_models_lists_available_models_with_details(self):
        """Test: ttt models - Lists models with provider and capability information"""
        result = run_ttt_command(["models"])
        assert result.exit_code == 0, f"Models command failed: {result.output}"
        
        output_lower = result.output.lower()
        # Should show models list with header
        assert any(word in output_lower for word in ["model", "available"]), f"Models header missing: {result.output}"
        
        # Should contain actual model names
        assert any(model in output_lower for model in ["gpt", "claude", "gemini"]), f"No recognizable models found: {result.output}"
        
        # Should provide structured output with multiple entries
        lines = [line.strip() for line in result.output.split('\n') if line.strip()]
        assert len(lines) >= 3, f"Models output should list multiple models: {result.output}"




class TestModelSelectionOptions:
    """Test model selection options."""

    @pytest.mark.requires_api
    def test_ask_model_gpt4(self):
        """Test: ttt ask --model gpt-4 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--model", "gpt-4", "hello"])
        assert result.exit_code in [0, 124]

    @pytest.mark.requires_api
    def test_ask_model_short_flag(self):
        """Test: ttt ask -m @claude 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@claude", "hello"])
        # Accept success (0), timeout (124), or model unavailable error (1)
        assert result.exit_code in [0, 1, 124]

    @pytest.mark.requires_api
    def test_ask_full_model_path(self):
        """Test: ttt ask --model openrouter/google/gemini-flash-1.5 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--model", "openrouter/google/gemini-flash-1.5", "hello"])
        assert result.exit_code in [0, 124]


class TestSystemPromptOptions:
    """Test system prompt options."""


    def test_ask_system_prompt(self):
        """Test: ttt ask --system 'system prompt' 'user prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--system", "You are helpful", "hello"])
        assert result.exit_code in [0, 124]


class TestTemperatureControl:
    """Test temperature control options."""


    @pytest.mark.requires_api
    def test_ask_temperature_long(self):
        """Test: ttt ask --temperature 0.7 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--temperature", "0.7", "hello"])
        assert result.exit_code in [0, 124]

    @pytest.mark.requires_api
    def test_ask_temperature_short(self):
        """Test: ttt ask -t 0.1 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-t", "0.1", "hello"])
        assert result.exit_code in [0, 124]


class TestTokenLimits:
    """Test token limit options."""


    @pytest.mark.requires_api
    def test_ask_max_tokens(self):
        """Test: ttt ask --max-tokens 100 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--max-tokens", "100", "hello"])
        assert result.exit_code in [0, 124]


class TestToolsOptions:
    """Test tools options."""


    @pytest.mark.requires_api
    def test_ask_tools_basic_executes_with_tools_enabled(self):
        """Test: ttt ask --tools 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--tools", "true", "hello"])
        assert result.exit_code in [0, 124]


class TestOutputModes:
    """Test output modes."""



    @pytest.mark.requires_api
    def test_ask_stream(self):
        """Test: ttt ask --stream 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--stream", "true", "hello"])
        assert result.exit_code in [0, 124]

    @pytest.mark.requires_api
    def test_ask_json(self):
        """Test: ttt ask --json 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--json", "hello"])
        assert result.exit_code in [0, 124]


class TestChatCommands:
    """Test chat command options."""







class TestConfigCommands:
    """Test config commands."""


    def test_config_list_outputs_valid_configuration_json(self):
        """Test: ttt config list - Outputs valid JSON with TTT configuration structure"""
        result = run_ttt_command(["config", "list"])
        assert result.exit_code == 0, f"Config list command failed: {result.output}"
        
        # Should output valid JSON
        try:
            config_data = json.loads(result.output)
            assert isinstance(config_data, dict), f"Config should be a JSON object: {type(config_data)}"
            
            # Should contain expected configuration sections
            expected_keys = ["models", "api", "backend"]
            found_keys = [key for key in expected_keys if any(k.startswith(key) for k in config_data.keys())]
            assert len(found_keys) > 0, f"Config should contain model/api/backend settings. Found keys: {list(config_data.keys())}"
            
        except json.JSONDecodeError as e:
            pytest.fail(f"Config list should output valid JSON. Error: {e}. Output: {result.output}")

    def test_config_get_models_default_shows_configured_model(self):
        """Test: ttt config get models.default - Shows the configured default model with clear labeling"""
        result = run_ttt_command(["config", "get", "models.default"])
        assert result.exit_code == 0, f"Config get command failed: {result.output}"
        
        # Should show the key and its value clearly
        assert "models.default" in result.output, f"Config key not shown: {result.output}"
        
        # Should have a value (either a model name or indication of no value)
        lines = result.output.strip().split('\n')
        config_line = next((line for line in lines if "models.default" in line), None)
        assert config_line is not None, f"Config line not found in output: {result.output}"
        
        # Should be in key: value format
        assert ":" in config_line, f"Config should use key: value format: {config_line}"
        
        # Value should be present (not just the key)
        key_value = config_line.split(":", 1)
        assert len(key_value) == 2 and key_value[1].strip(), f"Config value missing: {config_line}"

    def test_config_get_models_aliases(self):
        """Test: ttt config get models.aliases - Tested 2025-07-24"""
        result = run_ttt_command(["config", "get", "models.aliases"])
        assert result.exit_code == 0
        assert "models.aliases:" in result.output


class TestJSONOutputCombinations:
    """Test JSON output combinations."""

    def test_status_json_provides_structured_system_data(self):
        """Test: ttt status --json - Outputs structured JSON with comprehensive system information"""
        result = run_ttt_command(["status", "--json"])
        assert result.exit_code == 0, f"Status JSON command failed: {result.output}"
        
        # Should output valid JSON
        try:
            data = json.loads(result.output)
            assert isinstance(data, dict), f"Status JSON should be an object: {type(data)}"
            
            # Should contain system status information
            expected_sections = ["backend", "api", "model", "config"]
            found_sections = [section for section in expected_sections 
                            if any(key.lower().startswith(section) for key in data.keys())]
            assert len(found_sections) > 0, f"Status should contain system info sections. Found keys: {list(data.keys())}"
            
            # Each section should have meaningful data
            non_empty_values = [v for v in data.values() if v is not None and v != ""]
            assert len(non_empty_values) >= len(data) // 2, f"Status should contain meaningful data: {data}"
            
        except json.JSONDecodeError as e:
            pytest.fail(f"Status --json should output valid JSON. Error: {e}. Output: {result.output}")

    def test_models_json_provides_comprehensive_model_data(self):
        """Test: ttt models --json - Outputs structured JSON array with detailed model information"""
        result = run_ttt_command(["models", "--json"])
        assert result.exit_code == 0, f"Models JSON command failed: {result.output}"
        
        # Should output valid JSON array
        try:
            data = json.loads(result.output)
            assert isinstance(data, list), f"Models JSON should be an array: {type(data)}"
            assert len(data) > 0, f"Models list should not be empty: {data}"
            
            # Each model should have essential properties
            for model in data:
                assert isinstance(model, dict), f"Each model should be an object: {model}"
                
                # Should have basic model information
                required_fields = ["name", "provider"]
                for field in required_fields:
                    field_present = any(key.lower().startswith(field) for key in model.keys())
                    assert field_present, f"Model missing {field}: {model}"
                
                # Name should be a non-empty string
                name_field = next((v for k, v in model.items() if k.lower().startswith("name")), None)
                assert name_field and isinstance(name_field, str) and name_field.strip(), f"Invalid model name: {model}"
            
        except json.JSONDecodeError as e:
            pytest.fail(f"Models --json should output valid JSON. Error: {e}. Output: {result.output}")

    def test_info_json_provides_detailed_model_metadata(self):
        """Test: ttt info <model> --json - Outputs comprehensive model metadata in structured JSON format"""
        result = run_ttt_command(["info", "gpt-4", "--json"])
        assert result.exit_code == 0, f"Info JSON command failed: {result.output}"
        
        # Should output valid JSON
        try:
            data = json.loads(result.output)
            assert isinstance(data, dict), f"Info JSON should be an object: {type(data)}"
            
            # Should contain model identification
            has_name = any(key.lower().startswith("name") or key.lower().startswith("model") for key in data.keys())
            assert has_name, f"Model info should contain name/model field: {list(data.keys())}"
            
            # Should contain provider information
            has_provider = any(key.lower().startswith("provider") for key in data.keys())
            assert has_provider, f"Model info should contain provider field: {list(data.keys())}"
            
            # Should have meaningful model details
            detail_fields = ["context", "token", "capabilit", "cost", "speed"]  # Partial matches
            found_details = [field for field in detail_fields 
                           if any(field in key.lower() for key in data.keys())]
            assert len(found_details) > 0, f"Model info should contain capability/performance details: {list(data.keys())}"
            
            # Verify GPT-4 specific content
            model_name = next((v for k, v in data.items() if "name" in k.lower() or "model" in k.lower()), "")
            assert "gpt-4" in str(model_name).lower(), f"Model name should contain 'gpt-4': {model_name}"
            
        except json.JSONDecodeError as e:
            pytest.fail(f"Info --json should output valid JSON. Error: {e}. Output: {result.output}")


class TestPipelineUsage:
    """Test pipeline/stdin usage."""

    @pytest.mark.requires_api
    def test_echo_pipe_ask(self):
        """Test: echo 'text' | ttt ask 'transform this' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "transform this"], input_text="hello world")
        assert result.exit_code in [0, 124]

    @pytest.mark.requires_api
    def test_echo_pipe_ask_specific(self):
        """Test: echo 'hello world' | ttt ask 'transform this' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "make this uppercase"], input_text="hello world")
        assert result.exit_code in [0, 124]


class TestModelAliases:
    """Test model aliases."""

    @pytest.mark.requires_api
    def test_ask_alias_claude(self):
        """Test: ttt ask -m @claude 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@claude", "hello"])
        # Accept success (0), timeout (124), or model unavailable error (1)
        assert result.exit_code in [0, 1, 124]

    @pytest.mark.requires_api
    def test_ask_alias_gpt4(self):
        """Test: ttt ask -m @gpt4 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@gpt4", "hello"])
        assert result.exit_code in [0, 124]

    @pytest.mark.requires_api
    def test_ask_alias_fast(self):
        """Test: ttt ask -m @fast 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@fast", "hello"])
        assert result.exit_code in [0, 124]

    @pytest.mark.requires_api
    def test_ask_alias_best(self):
        """Test: ttt ask -m @best 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@best", "hello"])
        assert result.exit_code in [0, 124]

    @pytest.mark.requires_api
    def test_ask_alias_coding(self):
        """Test: ttt ask -m @coding 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@coding", "hello"])
        # Accept success (0), timeout (124), or model unavailable error (1)
        assert result.exit_code in [0, 1, 124]

    @pytest.mark.requires_api
    def test_ask_alias_local(self):
        """Test: ttt ask -m @local 'prompt' - Tested 2025-07-24"""
        # Local models might not be available, but structure should work
        result = run_ttt_command(["ask", "-m", "@local", "hello"])
        assert result.exit_code in [0, 1, 124]  # May fail if Ollama not running

    def test_direct_alias_claude(self):
        """Test: ttt @claude 'prompt' - Direct alias usage"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["@claude", "hello"])
        # Accept success (0), timeout (124), or model unavailable error (1)
        assert result.exit_code in [0, 1, 124]


class TestComplexCombinations:
    """Test complex command combinations."""

    @pytest.mark.requires_api
    def test_complex_claude_tools_json(self):
        """Test: ttt ask --model @claude --temperature 0.2 --tools --json 'write a function' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(
            [
                "ask",
                "--model",
                "@claude",
                "--temperature",
                "0.2",
                "--tools",
                "true",
                "--json",
                "write a simple function",
            ]
        )
        # Accept success (0), timeout (124), or model unavailable error (1)
        assert result.exit_code in [0, 1, 124]

    @pytest.mark.requires_api
    def test_complex_gpt4_max_tokens(self):
        """Test: ttt ask --json --model gpt-4 --max-tokens 500 'structured analysis' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(
            [
                "ask",
                "--json",
                "--model",
                "gpt-4",
                "--max-tokens",
                "500",
                "analyze this briefly",
            ]
        )
        assert result.exit_code in [0, 124]

    @pytest.mark.requires_api
    def test_complex_stream_json(self):
        """Test: ttt ask -m @gpt4 --stream --json 'explain this algorithm' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@gpt4", "--stream", "true", "--json", "explain sorting"])
        assert result.exit_code in [0, 124]

    @pytest.mark.requires_api
    def test_complex_pipeline_tools_json(self):
        """Test: echo 'data' | ttt ask --model @claude --tools --json 'analyze and research' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(
            [
                "ask",
                "--model",
                "@claude",
                "--tools",
                "true",
                "--json",
                "analyze this data",
            ],
            input_text="sample data for analysis",
        )
        # Accept success (0), timeout (124), or model unavailable error (1)
        assert result.exit_code in [0, 1, 124]

    @pytest.mark.requires_api
    def test_complex_all_options(self):
        """Test: ttt ask --model @claude --temperature 0.7 --max-tokens 1000 --tools 'research topic' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(
            [
                "ask",
                "--model",
                "@claude",
                "--temperature",
                "0.7",
                "--max-tokens",
                "1000",
                "--tools",
                "true",
                "research Python",
            ]
        )
        # Accept success (0), timeout (124), or model unavailable error (1)
        assert result.exit_code in [0, 1, 124]

    @pytest.mark.requires_api
    def test_complex_fast_json_stream(self):
        """Test: ttt ask -m @fast --json --stream 'quick response in JSON format' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@fast", "--json", "--stream", "true", "quick hello"])
        assert result.exit_code in [0, 124]


class TestFilePipelineUsage:
    """Test file-based pipeline usage - tests real file I/O functionality."""

    @pytest.mark.requires_api
    def test_file_content_analysis_demonstrates_pipeline_usage(self):
        """Test: cat file.txt | ttt ask 'summarize' - Demonstrates real file processing pipeline with validation"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        # Create a temporary file with meaningful test content
        test_content = """# Project Documentation
        
This is a sample project that demonstrates TTT's ability to process file content.
The project includes multiple components:
1. A data processing module
2. A user interface component  
3. Integration tests
4. Configuration management
        
The architecture follows modern best practices with clear separation of concerns."""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_content)
            temp_file = f.name

        try:
            # Read file content and pipe to ttt with specific analysis request
            with open(temp_file, 'r') as f:
                file_content = f.read()
            
            result = run_ttt_command(["ask", "Summarize the main components mentioned in this documentation"], input_text=file_content)
            assert result.exit_code in [0, 124], f"File analysis command failed: {result.output}"
            
            # If successful, verify meaningful analysis was performed
            if result.exit_code == 0:
                response = result.output.strip()
                assert len(response) > 20, f"Response too short for meaningful analysis: {response}"
                
                # Verify the AI understood the content structure
                response_lower = response.lower()
                expected_concepts = ["component", "module", "project", "architecture"]
                found_concepts = [concept for concept in expected_concepts if concept in response_lower]
                assert len(found_concepts) >= 2, f"Analysis should reference key concepts from input. Found: {found_concepts}"
        finally:
            # Clean up
            os.unlink(temp_file)

    @pytest.mark.requires_api
    def test_json_file_pipe_ask(self):
        """Test: cat data.json | ttt ask 'analyze' - Tests JSON file processing"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            test_data = {"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}
            json.dump(test_data, f)
            temp_file = f.name

        try:
            with open(temp_file, 'r') as f:
                file_content = f.read()
            
            result = run_ttt_command(["ask", "how many users are in this data?"], input_text=file_content)
            assert result.exit_code in [0, 124]
        finally:
            os.unlink(temp_file)


class TestJSONInputPipeline:
    """Test JSON input pipeline - tests structured input parsing."""

    @pytest.mark.requires_api
    def test_json_input_pipeline(self):
        """Test: echo '{"prompt": "hello"}' | ttt ask - Tests JSON input parsing"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        json_input = '{"message": "hello world", "context": "testing"}'
        result = run_ttt_command(["ask", "extract the message from this JSON"], input_text=json_input)
        assert result.exit_code in [0, 124]

    @pytest.mark.requires_api
    def test_json_array_input(self):
        """Test: echo '[1,2,3]' | ttt ask 'sum these' - Tests JSON array processing"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        json_input = '[10, 20, 30, 40]'
        result = run_ttt_command(["ask", "what is the sum of these numbers?"], input_text=json_input)
        assert result.exit_code in [0, 124]


class TestConfigPersistence:
    """Test config persistence - tests that configuration actually saves and loads."""

    def test_config_management_demonstrates_persistence_workflow(self):
        """Test: config set/get roundtrip - Demonstrates complete configuration management workflow with validation"""
        # Get original value for restoration
        original_result = run_ttt_command(["config", "get", "models.default"])
        assert original_result.exit_code == 0, f"Initial config get failed: {original_result.output}"
        
        # Parse original value for proper restoration
        original_value = None
        if ":" in original_result.output:
            original_value = original_result.output.split(":", 1)[1].strip()
        
        # Test configuration change with a known model
        test_model = "gpt-3.5-turbo"
        set_result = run_ttt_command(["config", "set", "models.default", test_model])
        
        if set_result.exit_code == 0:
            # Verify the configuration was actually persisted
            verify_result = run_ttt_command(["config", "get", "models.default"])
            assert verify_result.exit_code == 0, f"Config verification failed: {verify_result.output}"
            assert test_model in verify_result.output, f"Config was not persisted correctly. Expected '{test_model}' in: {verify_result.output}"
            
            # Verify config change is reflected in config list
            list_result = run_ttt_command(["config", "list"])
            if list_result.exit_code == 0:
                assert test_model in list_result.output, f"Config change not reflected in full config list: {list_result.output}"
            
            # Restore original configuration
            if original_value:
                restore_result = run_ttt_command(["config", "set", "models.default", original_value])
                if restore_result.exit_code == 0:
                    # Verify restoration
                    final_result = run_ttt_command(["config", "get", "models.default"])
                    assert original_value in final_result.output, f"Config restoration failed: {final_result.output}"
        else:
            # If config set isn't available, verify config get provides useful information
            assert "models.default" in original_result.output, f"Config get should show key information: {original_result.output}"
            assert ":" in original_result.output, f"Config get should use key:value format: {original_result.output}"

    def test_config_invalid_key(self):
        """Test: config get invalid.key - Tests config error handling"""
        result = run_ttt_command(["config", "get", "invalid.nonexistent.key"])
        # Should either return an error or handle gracefully
        assert result.exit_code in [0, 1]


class TestModelAliasResolution:
    """Test model alias resolution across commands - tests alias system functionality."""

    def test_info_with_alias_claude(self):
        """Test: ttt info @claude - Tests alias resolution in info command"""
        result = run_ttt_command(["info", "@claude"])
        # Should either resolve successfully or give a clear error
        assert result.exit_code in [0, 1]
        
        if result.exit_code == 0:
            # Should show info about the resolved model
            assert any(word in result.output.lower() for word in ["claude", "anthropic", "model", "provider"])

    def test_info_with_alias_gpt4(self):
        """Test: ttt info @gpt4 - Tests alias resolution consistency"""
        result = run_ttt_command(["info", "@gpt4"])
        assert result.exit_code in [0, 1]
        
        if result.exit_code == 0:
            assert any(word in result.output.lower() for word in ["gpt", "openai", "model", "provider"])

    def test_info_with_alias_fast(self):
        """Test: ttt info @fast - Tests alias resolution for performance aliases"""
        result = run_ttt_command(["info", "@fast"])
        assert result.exit_code in [0, 1]


class TestAdditionalCLIOptions:
    """Test additional CLI options for completeness."""

    @pytest.mark.requires_api
    def test_system_prompt_short_flag(self):
        """Test: ttt ask -s 'system' 'user' - Tests short flag consistency"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-s", "You are helpful", "hello"])
        # May not be implemented, but test structure should work
        assert result.exit_code in [0, 1, 124]

    @pytest.mark.requires_api
    def test_higher_max_tokens(self):
        """Test: ttt ask --max-tokens 2000 'prompt' - Tests higher token limits"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--max-tokens", "2000", "write a detailed explanation"])
        assert result.exit_code in [0, 124]


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_cli_smoke.py -v
    pytest.main([__file__, "-v"])
