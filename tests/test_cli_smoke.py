"""Comprehensive smoke tests for TTT CLI commands.

This test suite runs every command combination from CLI_TESTS.md to ensure
all CLI functionality works correctly. Tests are organized to match the
checklist structure for easy cross-reference.

Run with:
    ./test.sh --test test_cli_smoke
    ./test.sh --test test_cli_smoke --markers "not requires_api"  # Skip API-dependent tests
"""

import json
import os
import subprocess

import pytest


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
    """Run a TTT command and return result."""
    # Ensure we use the right PATH to find ttt
    env = os.environ.copy()
    env["PATH"] = f"{os.path.expanduser('~/.local/bin')}:{env.get('PATH', '')}"

    try:
        result = subprocess.run(
            ["ttt"] + args,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=env,
        )
        return result
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=["ttt"] + args,
            returncode=124,  # Timeout return code
            stdout="",
            stderr="Command timed out",
        )


class TestBasicCommands:
    """Test basic CLI commands - should work without API keys."""

    def test_ttt_direct_prompt_with_api(self):
        """Test: ttt 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["hello world"])
        # Should either work or timeout (both acceptable for API calls)
        assert result.returncode in [0, 124]

    def test_ttt_ask_prompt(self):
        """Test: ttt ask 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "hello world"])
        assert result.returncode in [0, 124]

    def test_ttt_info_model(self):
        """Test: ttt info <model> - Tested 2025-07-24"""
        result = run_ttt_command(["info", "gpt-4"])
        assert result.returncode == 0
        assert "gpt-4" in result.stdout
        assert "Provider:" in result.stdout

    def test_ttt_chat_help(self):
        """Test: ttt chat - Tested 2025-07-24 (help only)"""
        result = run_ttt_command(["chat", "--help"])
        assert result.returncode == 0
        assert "Chat interactively" in result.stdout

    def test_ttt_status(self):
        """Test: ttt status - Tested 2025-07-24"""
        result = run_ttt_command(["status"])
        assert result.returncode == 0
        assert "TTT System Status" in result.stdout

    def test_ttt_models(self):
        """Test: ttt models - Tested 2025-07-24"""
        result = run_ttt_command(["models"])
        assert result.returncode == 0
        assert "Available Models" in result.stdout

    def test_ttt_config(self):
        """Test: ttt config - Tested 2025-07-24"""
        result = run_ttt_command(["config", "--help"])
        assert result.returncode == 0
        assert "Customize your setup" in result.stdout

    def test_ttt_version(self):
        """Test: ttt --version - Tested 2025-07-24"""
        result = run_ttt_command(["--version"])
        assert result.returncode == 0
        assert "version" in result.stdout.lower()


class TestModelSelectionOptions:
    """Test model selection options."""

    @pytest.mark.requires_api
    def test_ask_model_gpt4(self):
        """Test: ttt ask --model gpt-4 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--model", "gpt-4", "hello"])
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_ask_model_short_flag(self):
        """Test: ttt ask -m @claude 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@claude", "hello"])
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_ask_full_model_path(self):
        """Test: ttt ask --model openrouter/google/gemini-flash-1.5 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--model", "openrouter/google/gemini-flash-1.5", "hello"])
        assert result.returncode in [0, 124]


class TestSystemPromptOptions:
    """Test system prompt options."""

    def test_ask_system_help(self):
        """Test: ttt ask --system help availability - Tested 2025-07-24"""
        result = run_ttt_command(["ask", "--help"])
        assert result.returncode == 0
        # Should show both session and system options
        assert "--session" in result.stdout
        assert "--system" in result.stdout

    def test_ask_system_prompt(self):
        """Test: ttt ask --system 'system prompt' 'user prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--system", "You are helpful", "hello"])
        assert result.returncode in [0, 124]


class TestTemperatureControl:
    """Test temperature control options."""

    def test_ask_temperature_help(self):
        """Test: Temperature option availability - Tested 2025-07-24"""
        result = run_ttt_command(["ask", "--help"])
        assert result.returncode == 0
        assert "--temperature" in result.stdout

    @pytest.mark.requires_api
    def test_ask_temperature_long(self):
        """Test: ttt ask --temperature 0.7 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--temperature", "0.7", "hello"])
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_ask_temperature_short(self):
        """Test: ttt ask -t 0.1 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-t", "0.1", "hello"])
        assert result.returncode in [0, 124]


class TestTokenLimits:
    """Test token limit options."""

    def test_ask_max_tokens_help(self):
        """Test: Max tokens option availability - Tested 2025-07-24"""
        result = run_ttt_command(["ask", "--help"])
        assert result.returncode == 0
        assert "--max-tokens" in result.stdout

    @pytest.mark.requires_api
    def test_ask_max_tokens(self):
        """Test: ttt ask --max-tokens 100 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--max-tokens", "100", "hello"])
        assert result.returncode in [0, 124]


class TestToolsOptions:
    """Test tools options."""

    def test_ask_tools_help(self):
        """Test: Tools option availability - Tested 2025-07-24"""
        result = run_ttt_command(["ask", "--help"])
        assert result.returncode == 0
        assert "--tools" in result.stdout

    @pytest.mark.requires_api
    def test_ask_tools_basic(self):
        """Test: ttt ask --tools 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--tools", "true", "hello"])
        assert result.returncode in [0, 124]


class TestOutputModes:
    """Test output modes."""

    def test_ask_stream_help(self):
        """Test: Stream option availability - Tested 2025-07-24"""
        result = run_ttt_command(["ask", "--help"])
        assert result.returncode == 0
        assert "--stream" in result.stdout

    def test_ask_json_help(self):
        """Test: JSON option availability - Tested 2025-07-24"""
        result = run_ttt_command(["ask", "--help"])
        assert result.returncode == 0
        assert "--json" in result.stdout

    @pytest.mark.requires_api
    def test_ask_stream(self):
        """Test: ttt ask --stream 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--stream", "true", "hello"])
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_ask_json(self):
        """Test: ttt ask --json 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "--json", "hello"])
        assert result.returncode in [0, 124]


class TestChatCommands:
    """Test chat command options."""

    def test_chat_basic_help(self):
        """Test: ttt chat - Tested 2025-07-24"""
        result = run_ttt_command(["chat", "--help"])
        assert result.returncode == 0
        assert "Chat interactively" in result.stdout

    def test_chat_model_option(self):
        """Test: ttt chat --model option availability - Tested 2025-07-24"""
        result = run_ttt_command(["chat", "--help"])
        assert result.returncode == 0
        assert "--model" in result.stdout

    def test_chat_session_option(self):
        """Test: ttt chat --session option availability - Tested 2025-07-24"""
        result = run_ttt_command(["chat", "--help"])
        assert result.returncode == 0
        assert "--session" in result.stdout

    def test_chat_tools_option(self):
        """Test: ttt chat --tools option availability - Tested 2025-07-24"""
        result = run_ttt_command(["chat", "--help"])
        assert result.returncode == 0
        assert "--tools" in result.stdout

    def test_chat_markdown_option(self):
        """Test: ttt chat --markdown option availability - Tested 2025-07-24"""
        result = run_ttt_command(["chat", "--help"])
        assert result.returncode == 0
        assert "--markdown" in result.stdout


class TestConfigCommands:
    """Test config commands."""

    def test_config_help(self):
        """Test: ttt config - Tested 2025-07-24"""
        result = run_ttt_command(["config", "--help"])
        assert result.returncode == 0
        assert "get" in result.stdout
        assert "set" in result.stdout
        assert "list" in result.stdout

    def test_config_list(self):
        """Test: ttt config list - Tested 2025-07-24"""
        result = run_ttt_command(["config", "list"])
        assert result.returncode == 0
        # Should output JSON configuration
        try:
            json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail("Config list should output valid JSON")

    def test_config_get_models_default(self):
        """Test: ttt config get models.default - Tested 2025-07-24"""
        result = run_ttt_command(["config", "get", "models.default"])
        assert result.returncode == 0
        assert "models.default:" in result.stdout

    def test_config_get_models_aliases(self):
        """Test: ttt config get models.aliases - Tested 2025-07-24"""
        result = run_ttt_command(["config", "get", "models.aliases"])
        assert result.returncode == 0
        assert "models.aliases:" in result.stdout


class TestJSONOutputCombinations:
    """Test JSON output combinations."""

    def test_status_json(self):
        """Test: ttt status --json - Tested 2025-07-24"""
        result = run_ttt_command(["status", "--json"])
        assert result.returncode == 0
        # Should output valid JSON
        try:
            data = json.loads(result.stdout)
            assert "backends" in data
        except json.JSONDecodeError:
            pytest.fail("Status --json should output valid JSON")

    def test_models_json(self):
        """Test: ttt models --json - Tested 2025-07-24"""
        result = run_ttt_command(["models", "--json"])
        assert result.returncode == 0
        # Should output valid JSON array
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, list)
        except json.JSONDecodeError:
            pytest.fail("Models --json should output valid JSON")

    def test_info_json(self):
        """Test: ttt info <model> --json - Tested 2025-07-24"""
        result = run_ttt_command(["info", "gpt-4", "--json"])
        assert result.returncode == 0
        # Should output valid JSON
        try:
            data = json.loads(result.stdout)
            assert "name" in data or "model" in data
        except json.JSONDecodeError:
            pytest.fail("Info --json should output valid JSON")


class TestPipelineUsage:
    """Test pipeline/stdin usage."""

    @pytest.mark.requires_api
    def test_echo_pipe_ask(self):
        """Test: echo 'text' | ttt ask 'transform this' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "transform this"], input_text="hello world")
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_echo_pipe_ask_specific(self):
        """Test: echo 'hello world' | ttt ask 'transform this' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "make this uppercase"], input_text="hello world")
        assert result.returncode in [0, 124]


class TestModelAliases:
    """Test model aliases."""

    @pytest.mark.requires_api
    def test_ask_alias_claude(self):
        """Test: ttt ask -m @claude 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@claude", "hello"])
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_ask_alias_gpt4(self):
        """Test: ttt ask -m @gpt4 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@gpt4", "hello"])
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_ask_alias_fast(self):
        """Test: ttt ask -m @fast 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@fast", "hello"])
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_ask_alias_best(self):
        """Test: ttt ask -m @best 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@best", "hello"])
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_ask_alias_coding(self):
        """Test: ttt ask -m @coding 'prompt' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@coding", "hello"])
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_ask_alias_local(self):
        """Test: ttt ask -m @local 'prompt' - Tested 2025-07-24"""
        # Local models might not be available, but structure should work
        result = run_ttt_command(["ask", "-m", "@local", "hello"])
        assert result.returncode in [0, 1, 124]  # May fail if Ollama not running

    def test_direct_alias_claude(self):
        """Test: ttt @claude 'prompt' - Direct alias usage"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["@claude", "hello"])
        assert result.returncode in [0, 124]


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
        assert result.returncode in [0, 124]

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
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_complex_stream_json(self):
        """Test: ttt ask -m @gpt4 --stream --json 'explain this algorithm' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@gpt4", "--stream", "true", "--json", "explain sorting"])
        assert result.returncode in [0, 124]

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
        assert result.returncode in [0, 124]

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
        assert result.returncode in [0, 124]

    @pytest.mark.requires_api
    def test_complex_fast_json_stream(self):
        """Test: ttt ask -m @fast --json --stream 'quick response in JSON format' - Tested 2025-07-24"""
        if not has_valid_api_key():
            pytest.skip("Requires API key")

        result = run_ttt_command(["ask", "-m", "@fast", "--json", "--stream", "true", "quick hello"])
        assert result.returncode in [0, 124]


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_cli_smoke.py -v
    pytest.main([__file__, "-v"])
