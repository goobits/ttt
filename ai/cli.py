#!/usr/bin/env python3
"""Simple command-line interface for the AI library."""

import sys
import os
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

console = Console()


def show_help():
    """Show help message."""
    help_text = """
[bold blue]AI Library - Unified AI Interface[/bold blue]

[bold green]Usage:[/bold green]
  ai "Your question here"                      # Basic usage
  ai "Question" --model MODEL                  # Specify model
  ai "Question" --offline                      # Force local backend (Ollama)
  ai "Question" --online                       # Force cloud backend
  ai "Question" --code                         # Coding-optimized response
  ai "Question" --stream                       # Stream response
  ai "Question" --verbose                      # Show details
  ai "Question" --tools "module:function,..."  # Use tools/functions
  ai --chat                                    # Interactive chat mode (in development)
  
[bold green]Commands:[/bold green]
  ai backend-status                            # Check backend status
  ai models-list                               # List available models
  ai tools-list                                # List available tools
  ai --help                                    # Show this help

[bold green]Examples:[/bold green]
  ai "What is Python?"
  ai "Explain quantum computing" --stream
  ai "Tell me a joke" --model openrouter/google/gemini-flash-1.5
  ai "Debug this code" --code --verbose
  ai "Local question" --offline --model llama2
  ai "Cloud question" --online --model gpt-4
  ai --chat --model claude-3-sonnet            # Interactive chat (in development)
  ai --chat --offline                          # Private chat (in development)
  ai "What's the weather?" --tools "weather:get_weather"
  ai "Calculate this" --tools "math:add,math:multiply"
  
[bold green]Environment:[/bold green]
  Set OPENROUTER_API_KEY=your-key for cloud models
  Set OPENAI_API_KEY=your-key for OpenAI models
  Set ANTHROPIC_API_KEY=your-key for Anthropic models
    """
    console.print(help_text)


def show_backend_status():
    """Show backend status."""
    console.print("[bold blue]Backend Status:[/bold blue]")
    console.print()

    # Check local backend
    try:
        import ai.backends.local as local_module

        local = local_module.LocalBackend()
        if local.is_available:
            console.print("✅ [green]Local Backend:[/green] Available")
            console.print(f"   Base URL: {local.base_url}")
            console.print(f"   Default Model: {local.default_model}")
        else:
            console.print("❌ [red]Local Backend:[/red] Not available")
    except Exception as e:
        console.print(f"❌ [red]Local Backend:[/red] Error - {e}")

    console.print()

    # Check cloud backend
    try:
        import ai.backends.cloud as cloud_module

        cloud = cloud_module.CloudBackend()
        if cloud.is_available:
            console.print("✅ [green]Cloud Backend:[/green] Available")
            console.print(f"   Default Model: {cloud.default_model}")

            # Check API keys
            keys_found = []
            for key_name in [
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "GOOGLE_API_KEY",
                "OPENROUTER_API_KEY",
            ]:
                if os.getenv(key_name):
                    keys_found.append(key_name.replace("_API_KEY", ""))

            if keys_found:
                console.print(f"   API Keys: {', '.join(keys_found)}")
            else:
                console.print("   [yellow]API Keys:[/yellow] None configured")
        else:
            console.print("❌ [red]Cloud Backend:[/red] Not available")
    except Exception as e:
        console.print(f"❌ [red]Cloud Backend:[/red] Error - {e}")


def show_models_list():
    """Show available models."""
    console.print("[bold blue]Available Models:[/bold blue]")
    console.print()

    # Local models
    console.print("[bold green]Local Models (Ollama):[/bold green]")
    try:
        import ai.backends.local as local_module

        local = local_module.LocalBackend()
        if local.is_available:
            # Try to get models from Ollama
            import httpx

            try:
                response = httpx.get(f"{local.base_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    if models:
                        for model in models:
                            console.print(f"  • {model['name']}")
                    else:
                        console.print("  No local models found")
                else:
                    console.print("  Could not fetch local models")
            except Exception:
                console.print("  Ollama not running or not accessible")
        else:
            console.print("  Local backend not available")
    except Exception as e:
        console.print(f"  Error: {e}")

    console.print()

    # Cloud models
    console.print("[bold green]Cloud Models (examples):[/bold green]")
    console.print("  OpenRouter:")
    console.print("    • openrouter/google/gemini-flash-1.5")
    console.print("    • openrouter/anthropic/claude-3-haiku")
    console.print("    • openrouter/meta-llama/llama-3-8b-instruct")
    console.print("    • openrouter/openai/gpt-4o-mini")
    console.print()
    console.print("  Direct:")
    console.print("    • gpt-3.5-turbo (OpenAI)")
    console.print("    • claude-3-sonnet-20240229 (Anthropic)")
    console.print("    • gemini-pro (Google)")


def show_tools_list():
    """Show available tools."""
    console.print("[bold blue]Available Tools:[/bold blue]")
    console.print()

    try:
        import ai.tools.registry as tools_registry
        import ai.tools as tools_module

        # Get all tools grouped by category
        registry = tools_registry.get_registry()
        all_tools = tools_module.list_tools()

        # Group by category
        by_category = {}
        for tool in all_tools:
            category = tool.category or "general"
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(tool)

        # Display by category
        for category, tools in sorted(by_category.items()):
            console.print(f"[bold green]{category.title()} Tools:[/bold green]")
            for tool in sorted(tools, key=lambda t: t.name):
                # Truncate description if too long
                desc = tool.description or "No description"
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                console.print(f"  • [bold]{tool.name}[/bold] - {desc}")
            console.print()

        console.print(f"[dim]Total: {len(all_tools)} tools available[/dim]")
        console.print("[dim]Use --tools flag to include tools in your requests[/dim]")

    except Exception as e:
        console.print(f"[red]Error listing tools:[/red] {e}")
        console.print("[dim]Make sure the AI library is properly installed[/dim]")


def detect_best_backend(args):
    """Detect the best available backend."""
    # Check if API keys are available for cloud backend
    cloud_available = any([
        os.getenv("OPENROUTER_API_KEY"),
        os.getenv("OPENAI_API_KEY"), 
        os.getenv("ANTHROPIC_API_KEY"),
        os.getenv("GOOGLE_API_KEY")
    ])
    
    # Check if local backend (Ollama) is available
    local_available = False
    try:
        import ai.backends.local as local_module
        local = local_module.LocalBackend()
        local_available = local.is_available
    except Exception:
        pass
    
    # Prefer cloud if available, fallback to local
    if cloud_available:
        return "cloud"
    elif local_available:
        return "local"
    else:
        # No backends available - will show error later
        return "cloud"  # Default to cloud for better error messages


def apply_coding_optimization(args, kwargs):
    """Apply optimizations for coding requests."""
    # Use coding-optimized system prompt if none specified
    if not args.get("system"):
        kwargs["system"] = "You are a helpful coding assistant. Provide clear, well-commented code examples and explanations."
    
    # Prefer coding-optimized models if available
    if not args.get("model"):
        if args["backend"] == "cloud":
            # Use Claude for coding (good at code)
            kwargs["model"] = "openrouter/anthropic/claude-3-sonnet"
        elif args["backend"] == "local":
            # Prefer code-specific local models
            kwargs["model"] = "codellama:latest"
    
    # Slightly lower temperature for more focused responses
    if args.get("temperature") is None:
        kwargs["temperature"] = 0.3
        
    return kwargs


def is_coding_request(prompt: str) -> bool:
    """Detect if a prompt is likely coding-related."""
    coding_keywords = [
        "code", "function", "python", "javascript", "java", "c++", "rust",
        "debug", "error", "bug", "algorithm", "implement", "write a program",
        "script", "api", "database", "sql", "html", "css", "react", "node",
        "variable", "loop", "class", "method", "import", "library", "framework"
    ]
    
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in coding_keywords)


def check_backend_available(backend):
    """Check if the specified backend is actually available."""
    if backend == "cloud":
        # Check if any API keys are configured
        return any([
            os.getenv("OPENROUTER_API_KEY"),
            os.getenv("OPENAI_API_KEY"), 
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("GOOGLE_API_KEY")
        ])
    elif backend == "local":
        # Check if Ollama is running
        try:
            import ai.backends.local as local_module
            local = local_module.LocalBackend()
            return local.is_available
        except Exception:
            return False
    return False


def show_setup_guidance():
    """Show helpful setup guidance when no backends are configured."""
    console.print("[red]❌ No AI backends configured.[/red]")
    console.print()
    
    help_text = """[bold green]Setup Options:[/bold green]

[bold]1. Online AI (requires API key):[/bold]
   • Get an API key from one of these providers:
     - OpenRouter (recommended): https://openrouter.ai
     - OpenAI: https://platform.openai.com
     - Anthropic: https://console.anthropic.com
     - Google: https://ai.google.dev
   • Add your key to .env file:
     [cyan]OPENROUTER_API_KEY=your-key-here[/cyan]

[bold]2. Offline AI (requires Ollama):[/bold]
   • Install Ollama: [cyan]curl -fsSL https://ollama.com/install.sh | sh[/cyan]
   • Pull a model: [cyan]ollama pull llama2[/cyan]
   • Then use: [cyan]ai "question" --offline[/cyan]

[bold]3. Both (recommended):[/bold]
   • Configure API keys AND install Ollama for maximum flexibility
   • Use [cyan]--online[/cyan] or [cyan]--offline[/cyan] flags to choose

[bold green]Check Status:[/bold green]
   • Run [cyan]ai backend-status[/cyan] to see what's configured
   • Run [cyan]ai models-list[/cyan] to see available models

Choose your preferred setup and try again."""
    
    console.print(Panel(help_text, title="AI Setup Required", border_style="yellow"))


def handle_interactive_chat(args):
    """Handle interactive chat mode - simplified version without complex dependencies."""
    console.print("[bold blue]AI Interactive Chat Mode[/bold blue]")
    console.print("[red]⚠️ Chat mode is currently under development[/red]")
    console.print("[yellow]Please use basic queries instead: ai \"Your question here\"[/yellow]")
    console.print()
    
    # Show what would be configured
    console.print("[dim]Chat mode configuration (preview):[/dim]")
    config_info = []
    if args["backend"]:
        config_info.append(f"Backend: {args['backend']}")
    else:
        config_info.append("Backend: Auto-detected")
    
    if args["model"]:
        config_info.append(f"Model: {args['model']}")
    else:
        config_info.append("Model: Default")
        
    if args["offline"]:
        config_info.append("Mode: Offline (local models)")
    elif args["online"]:
        config_info.append("Mode: Online (cloud models)")
    else:
        config_info.append("Mode: Auto-selected")
        
    if args["code"]:
        config_info.append("Optimization: Coding mode enabled")
    
    if args["verbose"]:
        config_info.append("Verbose: Enabled")
    
    for line in config_info:
        console.print(f"  • {line}")
    
    console.print()
    console.print("[blue]ℹ️ Chat mode will support:[/blue]")
    console.print("  • Persistent conversation history")
    console.print("  • Session save/load")
    console.print("  • Interactive mode with context")
    console.print("  • All current AI features")
    console.print()
    console.print("[green]For now, use:[/green] [yellow]ai \"Your question here\"[/yellow]")
    
    # For testing, ask if they want to try a single question
    try:
        user_input = console.input("\n[dim]Test with a single question (or press Enter to exit):[/dim] ").strip()
        if user_input:
            console.print("[dim]Converting to single query...[/dim]")
            # Use the regular query flow
            args["command"] = "query"
            args["prompt"] = user_input
            # Remove chat-specific args
            args.pop("chat", None)
            # Continue with regular query processing
            return args
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
    except EOFError:
        console.print("\n[yellow]Cancelled[/yellow]")
    
    return None


def resolve_tools(tool_specs: List[str]) -> List:
    """Resolve tool specifications to actual tool objects.

    Args:
        tool_specs: List of tool specifications in format:
            - "module:function" - Import function from module
            - "function" - Use from global registry
            - "/path/to/file.py:function" - Import from file

    Returns:
        List of resolved tool objects
    """
    resolved_tools = []

    for spec in tool_specs:
        if ":" in spec:
            # Module:function or path:function format
            module_path, function_name = spec.rsplit(":", 1)

            try:
                if (
                    module_path.endswith(".py")
                    or "/" in module_path
                    or "\\" in module_path
                ):
                    # File path - load module from file
                    import importlib.util

                    spec_loader = importlib.util.spec_from_file_location(
                        "tool_module", module_path
                    )
                    if spec_loader and spec_loader.loader:
                        module = importlib.util.module_from_spec(spec_loader)
                        spec_loader.loader.exec_module(module)
                        if hasattr(module, function_name):
                            resolved_tools.append(getattr(module, function_name))
                        else:
                            console.print(
                                f"[yellow]Warning: Function '{function_name}' not found in {module_path}[/yellow]"
                            )
                else:
                    # Module name - import normally
                    import importlib

                    module = importlib.import_module(module_path)
                    if hasattr(module, function_name):
                        resolved_tools.append(getattr(module, function_name))
                    else:
                        console.print(
                            f"[yellow]Warning: Function '{function_name}' not found in module {module_path}[/yellow]"
                        )
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not load tool '{spec}': {e}[/yellow]"
                )
        else:
            # Just function name - try to get from registry
            import ai.tools.registry as tools_registry

            tool = tools_registry.get_tool(spec)
            if tool:
                resolved_tools.append(tool)
            else:
                console.print(
                    f"[yellow]Warning: Tool '{spec}' not found in registry[/yellow]"
                )

    return resolved_tools


def parse_chat_args(args):
    """Parse arguments for chat mode."""
    result = {
        "command": "chat",
        "model": None,
        "system": None,
        "backend": None,
        "temperature": None,
        "max_tokens": None,
        "verbose": False,
        "tools": [],
        "offline": False,
        "online": False,
        "code": False,
    }
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg.startswith("-") and arg != "-":
            if arg in ["--model", "-m"] and i + 1 < len(args):
                result["model"] = args[i + 1]
                i += 2
            elif arg in ["--system", "-s"] and i + 1 < len(args):
                result["system"] = args[i + 1]
                i += 2
            elif arg in ["--backend", "-b"] and i + 1 < len(args):
                result["backend"] = args[i + 1]
                i += 2
            elif arg in ["--temperature", "-t"] and i + 1 < len(args):
                result["temperature"] = float(args[i + 1])
                i += 2
            elif arg == "--max-tokens" and i + 1 < len(args):
                result["max_tokens"] = int(args[i + 1])
                i += 2
            elif arg in ["--verbose", "-v"]:
                result["verbose"] = True
                i += 1
            elif arg == "--tools" and i + 1 < len(args):
                tools_str = args[i + 1]
                result["tools"] = [t.strip() for t in tools_str.split(",") if t.strip()]
                i += 2
            elif arg == "--offline":
                result["offline"] = True
                result["backend"] = "local"
                i += 1
            elif arg == "--online":
                result["online"] = True
                result["backend"] = "cloud"
                i += 1
            elif arg == "--code":
                result["code"] = True
                i += 1
            elif arg == "--chat":
                # Skip the --chat flag itself
                i += 1
            else:
                i += 1
        else:
            i += 1
    
    return result


def parse_args():
    """Parse command line arguments manually."""
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        return {"command": "help"}

    if args[0] == "backend-status":
        return {"command": "backend-status"}

    if args[0] == "models-list":
        return {"command": "models-list"}

    if args[0] == "tools-list" or args[0] == "tools":
        return {"command": "tools-list"}

    # Check for chat mode first
    if "--chat" in args:
        return parse_chat_args(args)

    # Parse AI query
    result = {
        "command": "query",
        "prompt": None,
        "model": None,
        "system": None,
        "backend": None,  # Will auto-detect if None
        "temperature": None,
        "max_tokens": None,
        "stream": False,
        "verbose": False,
        "tools": [],
        "offline": False,
        "online": False,
        "code": False,
    }

    # Collect all non-flag arguments as potential prompt parts
    prompt_parts = []
    
    i = 0
    while i < len(args):
        arg = args[i]

        if arg.startswith("-") and arg != "-":
            if arg in ["--model", "-m"] and i + 1 < len(args):
                result["model"] = args[i + 1]
                i += 2
            elif arg in ["--system", "-s"] and i + 1 < len(args):
                result["system"] = args[i + 1]
                i += 2
            elif arg in ["--backend", "-b"] and i + 1 < len(args):
                result["backend"] = args[i + 1]
                i += 2
            elif arg in ["--temperature", "-t"] and i + 1 < len(args):
                result["temperature"] = float(args[i + 1])
                i += 2
            elif arg == "--max-tokens" and i + 1 < len(args):
                result["max_tokens"] = int(args[i + 1])
                i += 2
            elif arg == "--stream":
                result["stream"] = True
                i += 1
            elif arg in ["--verbose", "-v"]:
                result["verbose"] = True
                i += 1
            elif arg == "--tools" and i + 1 < len(args):
                # Parse comma-separated tool specifications
                tools_str = args[i + 1]
                result["tools"] = [t.strip() for t in tools_str.split(",") if t.strip()]
                i += 2
            elif arg == "--offline":
                result["offline"] = True
                result["backend"] = "local"
                i += 1
            elif arg == "--online":
                result["online"] = True
                result["backend"] = "cloud"
                i += 1
            elif arg == "--code":
                result["code"] = True
                i += 1
            elif arg == "--chat":
                # Skip --chat flag in query parsing (handled earlier)
                i += 1
            else:
                i += 1
        else:
            # Collect non-flag arguments as prompt parts
            prompt_parts.append(arg)
            i += 1
    
    # Join all prompt parts with spaces (supports flexible positioning)
    if prompt_parts:
        result["prompt"] = " ".join(prompt_parts)

    return result


def main():
    """Main CLI entry point."""
    # Set minimal logging for clean output
    import os
    import logging
    import contextlib

    os.environ["LITELLM_LOG"] = "CRITICAL"

    # Disable all the noisy loggers
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    logging.getLogger("litellm").setLevel(logging.CRITICAL)
    logging.getLogger("aiohttp").setLevel(logging.CRITICAL)
    logging.getLogger("aiohttp.client").setLevel(logging.CRITICAL)
    logging.getLogger("aiohttp.connector").setLevel(logging.CRITICAL)

    # Context manager to suppress cleanup warnings
    @contextlib.contextmanager
    def suppress_cleanup_warnings():
        import warnings
        import logging

        # Store original levels
        original_levels = {
            "aiohttp": logging.getLogger("aiohttp").level,
            "aiohttp.client": logging.getLogger("aiohttp.client").level,
            "aiohttp.connector": logging.getLogger("aiohttp.connector").level,
        }

        try:
            # Temporarily suppress specific warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*Task was destroyed.*")
                warnings.filterwarnings("ignore", message=".*sys.meta_path.*")
                warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*")
                warnings.filterwarnings("ignore", message=".*Client session is not closed.*")
                warnings.filterwarnings("ignore", message=".*Connector is closed.*")

                # Suppress aiohttp deletion warnings more aggressively
                for logger_name in original_levels:
                    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

                yield
        finally:
            # Restore original levels
            for logger_name, level in original_levels.items():
                logging.getLogger(logger_name).setLevel(level)

    try:
        args = parse_args()

        if args["command"] == "help":
            show_help()
            return

        if args["command"] == "backend-status":
            show_backend_status()
            return

        if args["command"] == "models-list":
            show_models_list()
            return

        if args["command"] == "tools-list":
            show_tools_list()
            return

        if args["command"] == "chat":
            result = handle_interactive_chat(args)
            if result is None:
                return  # User cancelled or chat mode not ready
            # If result is returned, continue with query processing
            args = result

        if args["command"] == "query":
            prompt = args["prompt"]

            if not prompt:
                show_help()
                return

            # Read from stdin if prompt is "-"
            if prompt == "-":
                prompt = sys.stdin.read().strip()
                if not prompt:
                    console.print("[red]No input provided[/red]")
                    sys.exit(1)

            # Show what we're doing if verbose
            if args["verbose"]:
                panel_content = f"[bold]Prompt:[/bold] {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
                if args["model"]:
                    panel_content += f"\n[bold]Model:[/bold] {args['model']}"
                if args["system"]:
                    panel_content += f"\n[bold]System:[/bold] {args['system'][:50]}{'...' if len(args['system']) > 50 else ''}"
                panel_content += f"\n[bold]Backend:[/bold] {args['backend']}"

                console.print(
                    Panel(panel_content, title="AI Request", border_style="blue")
                )
                console.print()

            # Smart backend detection if not specified
            if args["backend"] is None:
                args["backend"] = detect_best_backend(args)
                
            # Check if no backends are available and show setup guidance
            if not check_backend_available(args["backend"]):
                show_setup_guidance()
                return
            
            # Auto-detect coding requests and apply optimization
            if args["code"] or is_coding_request(prompt):
                if not args["code"] and args["verbose"]:
                    console.print("[dim]Auto-detected coding request, applying code optimization[/dim]")
                kwargs = apply_coding_optimization(args, {})
            else:
                kwargs = {}

            # Prepare arguments
            if args["model"]:
                kwargs["model"] = args["model"]
            elif args["backend"] == "cloud":
                # Default to OpenRouter model if using cloud and no model specified
                kwargs["model"] = "openrouter/google/gemini-flash-1.5"
            if args["system"]:
                kwargs["system"] = args["system"]
            if args["backend"]:
                kwargs["backend"] = args["backend"]
            if args["temperature"] is not None:
                kwargs["temperature"] = args["temperature"]
            if args["max_tokens"]:
                kwargs["max_tokens"] = args["max_tokens"]

            # Resolve tools if specified
            if args["tools"]:
                resolved_tools = resolve_tools(args["tools"])
                if resolved_tools:
                    kwargs["tools"] = resolved_tools
                    if args["verbose"]:
                        console.print(f"[dim]Loaded {len(resolved_tools)} tools[/dim]")
                        # Show tool execution stats if available
                        try:
                            import ai.tools.executor as executor_module

                            stats = executor_module.get_execution_stats()
                            if stats["total_calls"] > 0:
                                console.print(
                                    f"[dim]Tool execution stats: {stats['success_rate']:.1%} success rate, avg {stats['avg_execution_time']:.2f}s[/dim]"
                                )
                        except:
                            pass

            # Import here to avoid import errors
            import ai.api as api_module

            # Use context manager to suppress cleanup warnings
            with suppress_cleanup_warnings():
                if args["stream"]:
                    # Stream response
                    console.print("[dim]Streaming response...[/dim]")
                    console.print()

                    for chunk in api_module.stream(prompt, **kwargs):
                        console.print(chunk, end="")
                    console.print()  # Final newline
                else:
                    # Regular response
                    if args["verbose"]:
                        console.print("[dim]Generating response...[/dim]")

                    response = api_module.ask(prompt, **kwargs)

                    # Print response
                    console.print(str(response))

                    # Show metadata if verbose
                    if args["verbose"]:
                        console.print()
                        metadata = []
                        metadata.append(f"[bold]Model:[/bold] {response.model}")
                        metadata.append(f"[bold]Backend:[/bold] {response.backend}")
                        metadata.append(f"[bold]Time:[/bold] {response.time:.2f}s")
                        if hasattr(response, "tokens_in") and response.tokens_in:
                            metadata.append(
                                f"[bold]Tokens In:[/bold] {response.tokens_in}"
                            )
                        if hasattr(response, "tokens_out") and response.tokens_out:
                            metadata.append(
                                f"[bold]Tokens Out:[/bold] {response.tokens_out}"
                            )
                        if hasattr(response, "cost") and response.cost:
                            metadata.append(f"[bold]Cost:[/bold] ${response.cost:.4f}")

                        # Add tool call information if available
                        if hasattr(response, "tool_calls") and response.tool_calls:
                            metadata.append(
                                f"[bold]Tools Called:[/bold] {len(response.tool_calls)}"
                            )
                            for call in response.tool_calls:
                                status = "✓" if call.succeeded else "✗"
                                metadata.append(
                                    f"  {status} {call.name}({', '.join(f'{k}={v}' for k, v in call.arguments.items())})"
                                )

                        console.print(
                            Panel(
                                "\n".join(metadata),
                                title="Response Metadata",
                                border_style="green",
                            )
                        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        # Import exceptions for better error handling
        import ai.exceptions as exceptions_module

        # Provide user-friendly error messages based on exception type
        if isinstance(e, exceptions_module.APIKeyError):
            console.print(f"[red]❌ API Key Missing:[/red] {e}")
            console.print(
                f"[yellow]Set your API key in the .env file: {e.details.get('env_var', 'API_KEY')}[/yellow]"
            )
            sys.exit(1)
        elif isinstance(e, exceptions_module.ModelNotFoundError):
            console.print(f"[red]❌ Model Not Found:[/red] {e}")
            console.print(
                "[yellow]Run 'ai models-list' to see available models[/yellow]"
            )
            sys.exit(1)
        elif isinstance(e, exceptions_module.RateLimitError):
            console.print(f"[red]⏱️ Rate Limit Exceeded:[/red] {e}")
            retry_after = e.details.get("retry_after")
            if retry_after:
                console.print(
                    f"[yellow]Wait {retry_after} seconds before retrying[/yellow]"
                )
            else:
                console.print("[yellow]Wait a moment before retrying[/yellow]")
            sys.exit(1)
        elif isinstance(e, exceptions_module.BackendNotAvailableError):
            console.print(f"[red]🔌 Backend Not Available:[/red] {e}")
            console.print(
                "[yellow]Run 'ai backend-status' to check connectivity[/yellow]"
            )
            sys.exit(1)
        elif isinstance(e, exceptions_module.EmptyResponseError):
            console.print(f"[red]❌ Empty Response:[/red] {e}")
            console.print(
                "[yellow]The AI returned an empty response. Try rephrasing your question.[/yellow]"
            )
            sys.exit(1)
        else:
            # Generic error handling
            console.print(f"[red]❌ Error:[/red] {e}")
            if args.get("verbose"):
                import traceback

                console.print("\n[dim]Full traceback:[/dim]")
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
            else:
                console.print("[yellow]Use --verbose flag for more details[/yellow]")
            sys.exit(1)


if __name__ == "__main__":
    import warnings
    import atexit
    import signal
    import sys
    
    # Suppress aiohttp warnings at module level
    warnings.filterwarnings("ignore", message=".*Task was destroyed.*")
    warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*")
    warnings.filterwarnings("ignore", message=".*Client session is not closed.*")
    warnings.filterwarnings("ignore", message=".*Connector is closed.*")
    
    # Suppress stderr during cleanup
    def cleanup_handler():
        import os
        # Redirect stderr to devnull during cleanup
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)
        os.close(devnull)
    
    # Register cleanup for normal exit
    atexit.register(cleanup_handler)
    
    # Handle signals to avoid messy cleanup
    def signal_handler(signum, frame):
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
