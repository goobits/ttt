#!/usr/bin/env python3
"""Modern Click-based CLI for the AI library."""

import sys
import os
import io
from typing import Optional, List
import click
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv


# Load environment variables from .env file in project directory
from pathlib import Path
import os

# Try multiple strategies to find .env file
env_paths = []

# 1. Current working directory
env_paths.append(Path.cwd() / ".env")

# 2. Walk up from current directory to find .env
current_path = Path.cwd()
for parent in [current_path] + list(current_path.parents)[:5]:  # Limit to 5 levels up
    env_path = parent / ".env"
    if env_path not in env_paths:
        env_paths.append(env_path)

# 3. If in development (installed with --editable), check the source directory
# This handles the pipx --editable case
try:
    import ttt
    if hasattr(ttt, '__file__'):
        package_dir = Path(ttt.__file__).parent
        # Go up to find project root (where .env typically lives)
        project_root = package_dir.parent
        env_paths.append(project_root / ".env")
        # Also check one more level up in case of nested structure
        env_paths.append(project_root.parent / ".env")
except:
    pass

# 4. Common locations
env_paths.extend([
    Path.home() / ".env",
    Path("/workspace") / ".env",  # For development environments
])

# Load the first .env file found
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        # Debug: Show which .env was loaded
        if os.getenv("TTT_DEBUG"):
            print(f"Loaded .env from: {env_path}")
        break
else:
    # No .env file found - check if we should warn
    if not any(os.getenv(key) for key in ["OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]):
        # Only warn if no API keys are set at all
        if os.getenv("TTT_DEBUG"):
            print("Warning: No .env file found and no API keys in environment")

console = Console()

# Import TTT library modules
import ttt




def setup_logging_level(verbose=False, debug=False):
    """Setup logging level based on verbosity flags."""
    import logging
    
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    # Set root logger level
    logging.getLogger().setLevel(level)
    
    # Suppress third-party library logging unless debug mode
    if not debug:
        logging.getLogger('litellm').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)


@click.command(context_settings={"allow_extra_args": True})
@click.option('--version', is_flag=True, help='📋 Show version and system information')
@click.option('--model', '-m', help='🤖 Select your AI model for optimal results (e.g., gpt-4o, claude-3-5-sonnet)')
@click.option('--system', '-s', help='🎭 Define AI behavior and expertise with custom instructions')
@click.option('--temperature', '-t', type=float, help='🌡️  Balance creativity vs precision (0=focused, 1=creative)')
@click.option('--max-tokens', type=int, help='📝 Control response length for concise or detailed output')
@click.option('--tools', help='🔧 Activate AI capabilities: web search, code execution, file operations')
@click.option('--stream', is_flag=True, help='⚡ Watch responses appear in real-time as AI thinks')
@click.option('--verbose', '-v', is_flag=True, help='🔍 Show detailed processing information and diagnostics')
@click.option('--debug', is_flag=True, help='🐛 Enable comprehensive debugging for troubleshooting')
@click.option('--code', is_flag=True, help='💻 Optimize AI responses for programming and development tasks')
@click.option('--json', 'json_output', is_flag=True, help='📦 Export results as JSON for automation and scripting')
@click.option('--chat', is_flag=True, help='💬 Launch interactive conversation mode with memory')
@click.option('--status', is_flag=True, help='⚡ Verify system health and API connectivity')
@click.option('--models', is_flag=True, help='🤖 Browse all available AI models and their capabilities')
@click.option('--tools-list', is_flag=True, help='🔧 Discover all available AI tools and functions')
@click.option('--config', is_flag=True, help='⚙️  Access configuration management and preferences')
@click.argument('args', nargs=-1)
@click.pass_context
def main(ctx, version, model, system, temperature, max_tokens, 
         tools, stream, verbose, debug, code, json_output, 
         chat, status, models, tools_list, config, args):
    """🚀 TTT - Transform any text with intelligent AI processing
    
    TTT empowers developers, writers, and creators to process text with precision.
    From simple transformations to complex analysis - AI-powered and pipeline-ready.
    
    \b
    💡 Quick Wins:
      ttt "Fix grammar in this text"           # Instant text cleanup
      ttt "Summarize this article"             # Extract key insights
      echo "data.txt" | ttt "Convert to JSON"  # Pipeline integration
      ttt --chat                               # Interactive AI assistant
    
    \b
    🎯 Text Transformation & Analysis:
      ttt "Translate to Spanish"               # Language conversion
      ttt "Write a Python function to sort"    # Code generation
      ttt "What's the main theme here?"        # Content analysis
      ttt "Rewrite this professionally"        # Style transformation
    
    \b
    🌟 Why Choose TTT:
      • 100+ AI models with smart auto-selection
      • Stream responses in real-time or batch process
      • Built-in tools: web search, code execution, file operations
      • JSON output for scripting and automation
      • Works in pipelines, scripts, and interactive sessions
    
    \b
    🔑 Quick Setup:
      export OPENROUTER_API_KEY=your-key-here
      ttt status  # Verify your installation and API access
    """
    
    # Setup logging based on verbosity
    setup_logging_level(verbose, debug)
    
    if version:
        click.echo(f"TTT Library v{getattr(ttt, '__version__', '0.4.0')}")
        return
    
    # Handle special commands first
    if chat:
        start_chat_session(model, system, None, tools, None, verbose)
        return
    elif status:
        show_backend_status()
        return
    elif models:
        show_models_list()
        return
    elif tools_list:
        show_tools_list()
        return
    elif config:
        handle_config_command(args)
        return
    
    # Default behavior: treat args as prompt for ask command
    prompt = " ".join(args) if args else None
    
    # If no prompt, show help (unless reading from pipe)
    if prompt is None:
        # Check if there's actual stdin content by attempting a non-blocking read
        import select
        try:
            if sys.stdin.isatty() or not select.select([sys.stdin], [], [], 0)[0]:
                # Interactive terminal or no stdin data available - show help
                click.echo(ctx.get_help())
                return
        except (OSError, io.UnsupportedOperation):
            # Fallback: assume interactive if no clear pipe input
            click.echo(ctx.get_help())
            return
    
    ask_command(prompt, model, system, temperature, max_tokens, 
               tools, stream, verbose, code, json_output, allow_empty=False)


def start_chat_session(model, system, session_id, tools, load, verbose):
    """Start an interactive chat session."""
    
    # Parse tools
    tools_list = None
    if tools:
        tools_list = [tool.strip() for tool in tools.split(',')]
        tools_list = resolve_tools(tools_list)
    
    # Build session parameters
    kwargs = {}
    if model:
        kwargs['model'] = model
    if system:
        kwargs['system'] = system
    if session_id:
        kwargs['session_id'] = session_id
    if tools_list:
        kwargs['tools'] = tools_list
    
    try:
        # Load existing session if requested
        if load:
            from ttt.chat import PersistentChatSession
            session = PersistentChatSession.load(load)
            console.print(f"[green]Loaded session from {load}[/green]")
        else:
            session = ttt.chat(**kwargs).__enter__()
        
        console.print("[bold blue]AI Chat Session[/bold blue]")
        
        # Get chat help message from config
        try:
            from ttt.config import load_project_defaults
            project_defaults = load_project_defaults()
            help_message = project_defaults.get("chat", {}).get("commands", {}).get(
                "help_message", 
                "Type /exit to quit, /save <filename> to save session, /clear to clear history"
            )
        except Exception:
            help_message = "Type /exit to quit, /save <filename> to save session, /clear to clear history"
            
        console.print(help_message)
        console.print()
        
        turn_count = 0
        
        try:
            while True:
                try:
                    user_input = click.prompt(f"You ({turn_count + 1})", type=str, prompt_suffix=": ")
                except (EOFError, KeyboardInterrupt):
                    break
                
                if not user_input.strip():
                    continue
                
                # Handle chat commands
                if user_input.startswith('/'):
                    if user_input in ['/exit', '/quit']:
                        break
                    elif user_input.startswith('/save '):
                        filename = user_input[6:].strip()
                        if filename:
                            session.save(filename)
                            console.print(f"[green]Session saved to {filename}[/green]")
                        else:
                            console.print("[red]Please specify a filename[/red]")
                        continue
                    elif user_input == '/clear':
                        session.clear()
                        console.print("[yellow]Chat history cleared[/yellow]")
                        turn_count = 0
                        continue
                    elif user_input == '/help':
                        console.print("Commands: /exit, /quit, /save <file>, /clear, /help")
                        continue
                    else:
                        console.print(f"[red]Unknown command: {user_input}[/red]")
                        continue
                
                try:
                    response = session.ask(user_input)
                    console.print(f"[bold green]AI[/bold green]: {response}")
                    
                    if verbose:
                        console.print(f"[dim]Model: {response.model}, Time: {response.time:.2f}s[/dim]")
                    
                    turn_count += 1
                    
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    
        finally:
            if hasattr(session, '__exit__'):
                session.__exit__(None, None, None)
            
    except Exception as e:
        click.echo(f"Error starting chat session: {e}", err=True)
        sys.exit(1)


def handle_config_command(args):
    """Handle config command with arguments."""
    from ttt.config import get_config, configure, save_config
    
    try:
        if not args:
            # Show all configuration
            show_all_config()
        elif len(args) == 1:
            # Show specific key
            show_config_key(args[0])
        else:
            # Set key-value pair
            set_config_key(args[0], args[1])
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)




def ask_command(prompt, model, system, temperature, max_tokens, 
                tools, stream, verbose, code, json_output, allow_empty=False):
    """Internal function to handle AI questions."""
    
    # Handle missing prompt in interactive mode first
    if prompt is None and sys.stdin.isatty() and not allow_empty:
        click.echo("Error: Missing argument 'prompt'", err=True)
        sys.exit(1)
        
    # If allow_empty is True and no prompt and no stdin, show help
    if allow_empty and prompt is None and sys.stdin.isatty():
        return
    
    # Handle stdin input
    if prompt == '-' or (prompt is None and not sys.stdin.isatty()):
        # Reading from pipe
        try:
            input_text = sys.stdin.read().strip()
        except EOFError:
            input_text = ""
        
        if not input_text:
            # Handle empty input
            click.echo("Error: No input provided", err=True)
            sys.exit(1)
            
        # Try to parse as JSON first
        try:
            import json
            json_input = json.loads(input_text)
            
            # Extract prompt from various possible fields
            prompt = (json_input.get('prompt') or 
                     json_input.get('query') or 
                     json_input.get('message') or 
                     json_input.get('text') or 
                     json_input.get('content'))
            
            if not prompt:
                # If no recognized prompt field, treat entire JSON as prompt
                prompt = input_text
            else:
                # Extract other parameters from JSON if not already set
                if not model and json_input.get('model'):
                    model = json_input.get('model')
                if not system and json_input.get('system'):
                    system = json_input.get('system')
                if temperature is None and json_input.get('temperature') is not None:
                    temperature = json_input.get('temperature')
                if not max_tokens and json_input.get('max_tokens'):
                    max_tokens = json_input.get('max_tokens')
                if not tools and json_input.get('tools'):
                    tools = json_input.get('tools')
                if not stream and json_input.get('stream'):
                    stream = json_input.get('stream')
                    
        except json.JSONDecodeError:
            # Not valid JSON, treat as plain text
            prompt = input_text
            
    elif prompt is None:
        # If we got here without a prompt and not from stdin, something's wrong
        if allow_empty:
            return
        click.echo("Error: Missing argument 'prompt'", err=True)
        sys.exit(1)
    
    
    # Parse tools
    tools_list = None
    if tools:
        tools_list = [tool.strip() for tool in tools.split(',')]
        tools_list = resolve_tools(tools_list)
    
    # Build request parameters
    kwargs = {}
    if model:
        kwargs['model'] = model
    if system:
        kwargs['system'] = system
    if temperature is not None:
        kwargs['temperature'] = temperature
    if max_tokens:
        kwargs['max_tokens'] = max_tokens
    if tools_list:
        kwargs['tools'] = tools_list
    
    # Apply coding optimizations only if explicitly requested
    if code:
        apply_coding_optimization(kwargs)
    
    try:
        if stream:
            # Stream response
            if json_output:
                # For streaming with JSON, we need to collect chunks
                chunks = []
                for chunk in ttt.stream(prompt, **kwargs):
                    chunks.append(chunk)
                import json
                output = {"content": "".join(chunks), "streaming": True}
                click.echo(json.dumps(output))
            else:
                for chunk in ttt.stream(prompt, **kwargs):
                    click.echo(chunk, nl=False)
        else:
            # Regular response
            response = ttt.ask(prompt, **kwargs)
            
            if json_output:
                import json
                output = {
                    "content": str(response),
                    "model": response.model,
                    "backend": response.backend,
                    "time": response.time,
                    "streaming": False
                }
                if hasattr(response, 'tokens_in') and response.tokens_in:
                    output["tokens_in"] = response.tokens_in
                    output["tokens_out"] = response.tokens_out
                click.echo(json.dumps(output))
            else:
                click.echo(str(response).rstrip())
                
                if verbose:
                    click.echo(f"\nModel: {response.model}", err=True)
                    click.echo(f"Backend: {response.backend}", err=True)
                    click.echo(f"Time: {response.time:.2f}s", err=True)
                    if hasattr(response, 'tokens_in') and response.tokens_in:
                        click.echo(f"Tokens: {response.tokens_in} in, {response.tokens_out} out", err=True)
                    
    except Exception as e:
        if json_output:
            import json
            error_output = {"error": str(e)}
            click.echo(json.dumps(error_output))
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)






# Helper functions
def show_backend_status():
    """Show backend status."""
    console.print("[bold blue]Backend Status:[/bold blue]")
    console.print()

    # Check local backend
    try:
        import ttt.backends.local as local_module

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
        import ttt.backends.cloud as cloud_module

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
        import ttt.backends.local as local_module

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
    console.print("[bold green]Cloud Models:[/bold green]")
    
    # Try to get models from config
    try:
        from ttt.config_loader import get_project_config
        config = get_project_config()
        available_models = config.get("models", {}).get("available", {})
        
        # Group by provider
        providers = {}
        for model_name, model_info in available_models.items():
            if isinstance(model_info, dict):
                provider = model_info.get("provider", "unknown")
                if provider not in ["local", "unknown"]:
                    if provider not in providers:
                        providers[provider] = []
                    providers[provider].append(model_name)
        
        # Display models by provider
        for provider, models in sorted(providers.items()):
            if models:
                console.print(f"  • {provider.title()}: {', '.join(sorted(models[:3]))}")
                if len(models) > 3:
                    console.print(f"    and {len(models) - 3} more...")
                    
        if not providers:
            # Fallback to hardcoded if no config
            console.print("  • OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo")
            console.print("  • Anthropic: claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022")
            console.print("  • Google: gemini-1.5-pro, gemini-1.5-flash")
            
    except Exception:
        # Fallback to hardcoded if error
        console.print("  • OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo")
        console.print("  • Anthropic: claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022")
        console.print("  • Google: gemini-1.5-pro, gemini-1.5-flash")
        
    console.print("  • And many more via OpenRouter...")


def show_tools_list():
    """Show available tools."""
    console.print("[bold blue]Available Tools:[/bold blue]")
    console.print()
    
    try:
        from ttt.tools import list_tools, get_categories
        
        categories = get_categories()
        for category in sorted(categories):
            tools = list_tools(category=category)
            if tools:
                console.print(f"[bold green]{category.title()}:[/bold green]")
                for tool in sorted(tools, key=lambda t: t.name):
                    console.print(f"  • {tool.name}: {tool.description}")
                console.print()
    except Exception as e:
        console.print(f"Error listing tools: {e}")


def resolve_tools(tool_specs: List[str]) -> List:
    """Resolve tool specifications to actual tool functions."""
    tools = []
    
    try:
        from ttt.tools import get_tool, list_tools
        
        for spec in tool_specs:
            if ':' in spec:
                # Category:tool format
                category, tool_name = spec.split(':', 1)
                tool_list = list_tools(category=category)
                # Find tool by name in the list
                found_tool = None
                for tool_def in tool_list:
                    if tool_def.name == tool_name:
                        found_tool = tool_def.function
                        break
                if found_tool:
                    tools.append(found_tool)
                else:
                    console.print(f"[yellow]Warning: Tool {tool_name} not found in category {category}[/yellow]")
            else:
                # Just tool name
                tool_def = get_tool(spec)
                if tool_def:
                    tools.append(tool_def.function)
                else:
                    console.print(f"[yellow]Warning: Tool {spec} not found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error resolving tools: {e}[/red]")
    
    return tools


def is_coding_request(prompt: str) -> bool:
    """Detect if this is a coding-related request."""
    coding_keywords = [
        'function', 'class', 'method', 'code', 'script', 'program',
        'debug', 'fix', 'error', 'bug', 'implement', 'write',
        'python', 'javascript', 'java', 'c++', 'rust', 'go',
        'algorithm', 'data structure', 'api', 'database'
    ]
    
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in coding_keywords)


def apply_coding_optimization(kwargs):
    """Apply optimizations for coding requests."""
    # Lower temperature for more deterministic code
    if 'temperature' not in kwargs:
        kwargs['temperature'] = 0.3


def get_config_key_mapping():
    """Map user-friendly config keys to internal configuration paths."""
    return {
        'model': 'default_model',
        'backend': 'default_backend',
        'timeout': 'timeout',
        'retries': 'max_retries',
        'ollama_url': 'ollama_base_url',
        'openai_key': 'openai_api_key',
        'anthropic_key': 'anthropic_api_key',
        'google_key': 'google_api_key',
        'openrouter_key': 'openrouter_api_key',
    }


def show_all_config():
    """Display all current configuration settings."""
    from ttt.config import get_config
    
    config = get_config()
    console.print("[bold blue]Current Configuration:[/bold blue]")
    console.print()
    
    # Show main settings
    key_mapping = get_config_key_mapping()
    
    for user_key, config_key in key_mapping.items():
        value = getattr(config, config_key, None)
        if value is not None:
            # Mask sensitive values
            if 'key' in user_key.lower():
                masked_value = f"{str(value)[:8]}..." if len(str(value)) > 8 else "***"
                console.print(f"  {user_key}: {masked_value}")
            else:
                console.print(f"  {user_key}: {value}")
    
    console.print()
    console.print("[dim]Use 'ttt config <key> <value>' to change settings[/dim]")


def show_config_key(key):
    """Display a specific configuration value."""
    from ttt.config import get_config
    
    key_mapping = get_config_key_mapping()
    
    if key not in key_mapping:
        available_keys = ', '.join(key_mapping.keys())
        console.print(f"[red]Unknown config key '{key}'[/red]")
        console.print(f"Available keys: {available_keys}")
        return
    
    config = get_config()
    config_key = key_mapping[key]
    value = getattr(config, config_key, None)
    
    if value is not None:
        # Mask sensitive values
        if 'key' in key.lower():
            masked_value = f"{str(value)[:8]}..." if len(str(value)) > 8 else "***"
            console.print(f"{key}: {masked_value}")
        else:
            console.print(f"{key}: {value}")
    else:
        console.print(f"{key}: [dim]not set[/dim]")


def set_config_key(key, value):
    """Set a configuration value and persist it."""
    from ttt.config import get_config, configure, save_config
    
    key_mapping = get_config_key_mapping()
    
    if key not in key_mapping:
        available_keys = ', '.join(key_mapping.keys())
        console.print(f"[red]Unknown config key '{key}'[/red]")
        console.print(f"Available keys: {available_keys}")
        return
    
    config_key = key_mapping[key]
    
    # Type conversion for specific keys
    if key in ['timeout', 'retries']:
        try:
            value = int(value)
        except ValueError:
            console.print(f"[red]Error: '{key}' must be a number[/red]")
            return
    
    # Validate specific values
    if key == 'backend' and value not in ['local', 'cloud', 'auto']:
        console.print(f"[red]Error: backend must be 'local', 'cloud', or 'auto'[/red]")
        return
    
    # Apply the configuration change
    kwargs = {config_key: value}
    configure(**kwargs)
    
    # Save to persistent config file
    current_config = get_config()
    save_config(current_config)
    
    console.print(f"[green]Set {key} = {value}[/green]")
    console.print("[dim]Configuration saved to ~/.config/ai/config.yaml[/dim]")


if __name__ == "__main__":
    main()