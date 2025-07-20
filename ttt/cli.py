#!/usr/bin/env python3
"""Modern Click-based CLI for the AI library with subcommand structure."""

import sys
import os
import io
import warnings
from typing import Optional, List
import click
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Suppress the common aiohttp warning about pending tasks being destroyed
warnings.filterwarnings("ignore", message="Task was destroyed but it is pending!", category=RuntimeWarning)

# Also suppress via environment variable for asyncio
os.environ.setdefault("PYTHONWARNINGS", "ignore::RuntimeWarning")
try:
    from importlib.metadata import version as get_version
except ImportError:
    from importlib_metadata import version as get_version


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


def get_ttt_version():
    """Get the TTT version dynamically."""
    try:
        # Try the actual package name first
        from importlib.metadata import version as get_version
    except ImportError:
        from importlib_metadata import version as get_version
    
    try:
        return get_version('goobits-ttt')
    except Exception:
        try:
            return get_version('ttt')
        except Exception:
            return getattr(ttt, '__version__', 'unknown')


def setup_logging_level(verbose=False, debug=False, json_output=False):
    """Setup logging level based on verbosity flags."""
    import logging
    import asyncio
    from rich.logging import RichHandler
    from rich.console import Console
    
    if json_output:
        # Suppress ALL logging in JSON mode
        level = logging.CRITICAL
    elif debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    # Configure logging with Rich handler (unless in JSON mode)
    if not json_output and not logging.getLogger().handlers:
        console = Console()
        logging.basicConfig(
            level=level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(console=console, rich_tracebacks=True)],
        )
    else:
        # Set root logger level
        logging.getLogger().setLevel(level)
    
    # Suppress third-party library logging unless debug mode
    if not debug:
        logging.getLogger('litellm').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.CRITICAL)  # Suppress asyncio task warnings
        
        # Configure asyncio to handle task exceptions more gracefully
        def custom_exception_handler(loop, context):
            exception = context.get('exception')
            if exception:
                # Suppress specific aiohttp task destruction warnings
                if 'Task was destroyed but it is pending' in str(exception):
                    return  # Ignore this specific error
                # For other exceptions, use default behavior if verbose/debug
                if verbose or debug:
                    loop.default_exception_handler(context)
        
        # Try to set up the exception handler for the current loop if one exists
        try:
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(custom_exception_handler)
        except RuntimeError:
            # No current loop, that's fine
            pass


def resolve_model_alias(model: str) -> str:
    """Resolve model alias to full model name."""
    if model and model.startswith('@'):
        # Remove @ prefix
        alias = model[1:]
        
        # Load aliases from config
        try:
            from ttt.config_manager import ConfigManager
            config_manager = ConfigManager()
            merged_config = config_manager.get_merged_config()
            
            # Check aliases (includes both default and user-defined)
            aliases = merged_config.get('models', {}).get('aliases', {})
            if alias in aliases:
                return aliases[alias]
            
            # Also check model names that have aliases
            available_models = merged_config.get('models', {}).get('available', {})
            for model_name, model_info in available_models.items():
                if isinstance(model_info, dict):
                    model_aliases = model_info.get('aliases', [])
                    if alias in model_aliases:
                        return model_name
            
            # If not found, return original without @
            console.print(f"[yellow]Warning: Unknown model alias '@{alias}', using '{alias}'[/yellow]")
            return alias
        except Exception as e:
            console.print(f"[yellow]Warning: Could not resolve model alias: {e}[/yellow]")
            return alias
    
    # If this is a direct model name, check if we should route through OpenRouter
    if model and not model.startswith('openrouter/'):
        # Check what API keys are available
        has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        has_google = bool(os.getenv("GOOGLE_API_KEY"))
        
        # If only OpenRouter key is available, route common models through OpenRouter
        if has_openrouter and not (has_openai or has_anthropic or has_google):
            # Map common direct model names to OpenRouter equivalents
            openrouter_mappings = {
                'gpt-4o': 'openrouter/openai/gpt-4o',
                'gpt-4o-mini': 'openrouter/openai/gpt-4o-mini',
                'gpt-4': 'openrouter/openai/gpt-4',
                'gpt-3.5-turbo': 'openrouter/openai/gpt-3.5-turbo',
                'claude-3-5-sonnet-20241022': 'openrouter/anthropic/claude-3-5-sonnet-20241022',
                'claude-3-5-haiku-20241022': 'openrouter/anthropic/claude-3-5-haiku-20241022',
                'gemini-1.5-pro': 'openrouter/google/gemini-1.5-pro',
                'gemini-1.5-flash': 'openrouter/google/gemini-1.5-flash',
            }
            
            if model in openrouter_mappings:
                console.print(f"[dim]Routing {model} through OpenRouter...[/dim]")
                return openrouter_mappings[model]
    
    return model


def parse_tools_arg(tools: Optional[str]) -> Optional[str]:
    """Parse the tools argument according to new spec."""
    if tools is None:
        return None
    
    # If empty string or just --tools with no value, enable all tools
    if tools == "":
        # This will be handled by passing None to the ask function
        # which should enable all tools
        return "all"
    
    # Otherwise return the comma-separated list as-is
    return tools


class VersionAwareGroup(click.Group):
    """Custom group that adds version to help text."""
    
    def get_help(self, ctx):
        # Get the original help text
        original_help = super().get_help(ctx)
        
        # Replace the title line with version included
        lines = original_help.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('🚀 TTT - Transform'):
                lines[i] = f"  🚀 TTT {get_ttt_version()} - Transform any text with intelligent AI processing"
                break
        
        return '\n'.join(lines)


@click.group(cls=VersionAwareGroup, invoke_without_command=True,
             context_settings={'allow_interspersed_args': False})
@click.pass_context
@click.option('--version', is_flag=True, help='📋 Show version and system information')
@click.option('--model', '-m', help='🤖 Select your AI model (e.g., @claude, @gpt4, gpt-4o)')
@click.option('--system', '-s', help='🎭 Define AI behavior and expertise with custom instructions')
@click.option('--temperature', '-t', type=float, help='🌡️  Balance creativity vs precision (0=focused, 1=creative)')
@click.option('--max-tokens', type=int, help='📝 Control response length for concise or detailed output')
@click.option('--tools', default=None, help='🔧 Enable AI tools (empty=all, or specify: web,code)')
@click.option('--stream', is_flag=True, help='⚡ Watch responses appear in real-time as AI thinks')
@click.option('--verbose', '-v', is_flag=True, help='🔍 Show detailed processing information and diagnostics')
@click.option('--debug', is_flag=True, help='🐛 Enable comprehensive debugging for troubleshooting')
@click.option('--code', is_flag=True, help='💻 Optimize AI responses for programming and development tasks')
@click.option('--json', 'json_output', is_flag=True, help='📦 Export results as JSON for automation and scripting')
def main(ctx, version, model, system, temperature, max_tokens, 
         tools, stream, verbose, debug, code, json_output):
    """🚀 TTT - Transform any text with intelligent AI processing
    
    TTT empowers developers, writers, and creators to process text with precision.
    From simple transformations to complex analysis - AI-powered and pipeline-ready.
    
    \b
    💡 Quick Examples:
      ttt "Fix grammar in this text"           # Instant text cleanup
      ttt @claude "Summarize this article"     # Use Claude model  
      echo "data.txt" | ttt "Convert to JSON"  # Pipeline integration
      ttt chat                                 # Interactive AI conversation
    
    \b
    🎯 Subcommands:
      chat     💬 Launch interactive conversation mode
      status   ⚡ Verify system health and API connectivity
      models   🤖 Browse available AI models
      config   ⚙️  Manage configuration settings
    
    \b
    🔑 Quick Setup:
      export OPENROUTER_API_KEY=your-key-here
      ttt status  # Verify your installation
    """
    
    # Setup logging based on verbosity
    setup_logging_level(verbose, debug, json_output)
    
    if version:
        pkg_version = get_ttt_version()
        click.echo(f"TTT Library v{pkg_version}")
        return
    
    # If no subcommand, treat remaining args as direct prompt
    if ctx.invoked_subcommand is None:
        # Check if we have a prompt stored in context (from direct invocation)
        if hasattr(ctx, 'obj') and ctx.obj:
            prompt_text = ctx.obj
        else:
            # Get remaining args after options as prompt
            remaining_args = ctx.args
            prompt_text = " ".join(remaining_args) if remaining_args else None
        
        # If no prompt, show help (unless reading from pipe)
        if prompt_text is None:
            # Check if we're in a pipeline (stdin is not a tty)
            if sys.stdin.isatty():
                # Interactive terminal - show help immediately
                click.echo(ctx.get_help())
                return
            else:
                # We're in a pipeline - wait a reasonable amount of time for input
                import select
                try:
                    # Wait up to 30 seconds for input (for STT processing time)
                    if not select.select([sys.stdin], [], [], 30)[0]:
                        # Still no input after 30 seconds - show help
                        click.echo(ctx.get_help())
                        return
                except (OSError, io.UnsupportedOperation):
                    # Fallback: assume we should wait for stdin
                    pass
        
        # Resolve model alias
        if model:
            model = resolve_model_alias(model)
        
        # Parse tools argument
        tools = parse_tools_arg(tools)
        
        ask_command(prompt_text, model, system, temperature, max_tokens, 
                   tools, stream, verbose, code, json_output, allow_empty=False)


@main.command()
@click.option('--resume', is_flag=True, help='Continue the last chat session')
@click.option('--id', 'session_id', help='Use a named chat session')
@click.option('--list', 'list_sessions', is_flag=True, help='Show all chat sessions')
@click.option('--model', '-m', help='🤖 Select AI model (overrides default)')
@click.option('--system', '-s', help='🎭 Set system prompt for the session')
@click.option('--tools', help='🔧 Enable tools for this session')
@click.pass_context
def chat(ctx, resume, session_id, list_sessions, model, system, tools):
    """💬 Launch interactive conversation mode with memory."""
    from ttt.chat_sessions import ChatSessionManager
    
    # Initialize session manager
    session_manager = ChatSessionManager()
    
    # Handle --list
    if list_sessions:
        session_manager.display_sessions_table()
        return
    
    # Resolve model alias if provided
    if model:
        model = resolve_model_alias(model)
    
    # Parse tools
    if tools:
        tools = parse_tools_arg(tools)
        if tools == "all":
            tools = None  # Will enable all tools
        elif tools:
            tools = [t.strip() for t in tools.split(',')]
    
    # Load or create session
    if resume:
        session = session_manager.load_last_session()
        if not session:
            console.print("[yellow]No previous session found. Starting new session.[/yellow]")
            session = session_manager.create_session(model=model, system_prompt=system, tools=tools)
        else:
            console.print(f"[green]Resuming session: {session.id}[/green]")
            # Override settings if provided
            if model:
                session.model = model
            if system:
                session.system_prompt = system
            if tools:
                session.tools = tools
    elif session_id:
        session = session_manager.load_session(session_id)
        if not session:
            console.print(f"[red]Session '{session_id}' not found.[/red]")
            return
        console.print(f"[green]Loaded session: {session.id}[/green]")
        # Override settings if provided
        if model:
            session.model = model
        if system:
            session.system_prompt = system
        if tools:
            session.tools = tools
    else:
        # Create new session
        session = session_manager.create_session(model=model, system_prompt=system, tools=tools)
        console.print(f"[green]Started new session: {session.id}[/green]")
    
    # Show session info
    console.print("[bold blue]AI Chat Session[/bold blue]")
    if session.model:
        console.print(f"Model: {session.model}")
    if session.system_prompt:
        console.print(f"System: {session.system_prompt[:50]}...")
    console.print("Type /exit to quit, /clear to clear history, /help for commands")
    console.print()
    
    # Restore previous messages
    if session.messages:
        console.print("[dim]--- Previous conversation ---[/dim]")
        for msg in session.messages[-10:]:  # Show last 10 messages
            if msg.role == "user":
                console.print(f"[bold cyan]You:[/bold cyan] {msg.content}")
            else:
                console.print(f"[bold green]AI:[/bold green] {msg.content}")
        console.print("[dim]--- Continue conversation ---[/dim]")
        console.print()
    
    # Build kwargs for chat session
    chat_kwargs = {}
    if session.model:
        chat_kwargs['model'] = session.model
    if session.system_prompt:
        chat_kwargs['system'] = session.system_prompt
    if session.tools:
        chat_kwargs['tools'] = resolve_tools(session.tools)
    
    # Create chat session with context from previous messages
    messages = []
    if session.system_prompt:
        messages.append({"role": "system", "content": session.system_prompt})
    for msg in session.messages:
        messages.append({"role": msg.role, "content": msg.content})
    
    # Start chat loop
    try:
        # Use the chat API
        with ttt.chat(**chat_kwargs) as chat_session:
            # Restore message history
            if messages:
                chat_session.messages = messages
            
            while True:
                try:
                    user_input = click.prompt("You", type=str, prompt_suffix=": ")
                except (EOFError, KeyboardInterrupt):
                    console.print("\n[yellow]Chat session ended.[/yellow]")
                    break
                
                if not user_input.strip():
                    continue
                
                # Handle chat commands
                if user_input.startswith('/'):
                    if user_input in ['/exit', '/quit']:
                        console.print("[yellow]Chat session ended.[/yellow]")
                        break
                    elif user_input == '/clear':
                        session.messages = []
                        session_manager.save_session(session)
                        console.print("[yellow]Chat history cleared.[/yellow]")
                        # Reset chat session messages
                        chat_session.messages = [{"role": "system", "content": session.system_prompt}] if session.system_prompt else []
                        continue
                    elif user_input == '/help':
                        console.print("Commands:")
                        console.print("  /exit, /quit - End the chat session")
                        console.print("  /clear - Clear chat history")
                        console.print("  /help - Show this help message")
                        continue
                    else:
                        console.print(f"[red]Unknown command: {user_input}[/red]")
                        continue
                
                # Add user message to session
                session_manager.add_message(session, "user", user_input)
                
                try:
                    # Get AI response
                    response = chat_session.ask(user_input)
                    
                    # Display response
                    console.print(f"[bold green]AI:[/bold green] {response}")
                    
                    # Add AI response to session
                    session_manager.add_message(session, "assistant", str(response), 
                                              model=response.model if hasattr(response, 'model') else None)
                    
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    
    except Exception as e:
        console.print(f"[red]Error starting chat session: {e}[/red]")


@main.command()
def status():
    """⚡ Verify system health and API connectivity."""
    show_backend_status()


@main.command()
def models():
    """🤖 Browse all available AI models and their capabilities."""
    show_models_list()


@main.command()
@click.argument('action', required=False)
@click.argument('key', required=False)
@click.argument('value', required=False)
@click.option('--reset', is_flag=True, help='Reset configuration to defaults')
def config(action, key, value, reset):
    """⚙️ Access configuration management and preferences.
    
    \b
    Examples:
      ttt config                          # Show all configuration
      ttt config get models.default       # Show specific value
      ttt config set models.default gpt-4 # Set a value
      ttt config set alias.work gpt-4     # Set a model alias
      ttt config --reset                  # Reset to defaults
    """
    from ttt.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    
    # Handle reset
    if reset:
        # Confirm before resetting
        if click.confirm("Are you sure you want to reset configuration to defaults?"):
            config_manager.reset_config()
        return
    
    # Handle different actions
    if not action:
        # No action specified - show all config
        config_manager.display_config()
    elif action == 'get' and key:
        # Get specific value
        config_manager.show_value(key)
    elif action == 'set' and key and value:
        # Set specific value
        config_manager.set_value(key, value)
    elif action == 'set' and key and not value:
        # Special case: "ttt config set alias.foo" should show error
        console.print("[red]Error: Missing value for set command[/red]")
        console.print("Usage: ttt config set KEY VALUE")
    else:
        # Check if user meant to use old syntax
        if action and not key:
            # Maybe they typed "ttt config models.default"
            config_manager.show_value(action)
        else:
            console.print("[red]Invalid config command[/red]")
            console.print()
            console.print("Usage:")
            console.print("  ttt config                          # Show all configuration")
            console.print("  ttt config get KEY                  # Show specific value")  
            console.print("  ttt config set KEY VALUE            # Set a value")
            console.print("  ttt config set alias.NAME MODEL     # Set a model alias")
            console.print("  ttt config --reset                  # Reset to defaults")


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
    stdin_content = None
    if not sys.stdin.isatty():
        # We have piped input, read it
        try:
            stdin_content = sys.stdin.read().strip()
        except EOFError:
            stdin_content = ""
    
    if prompt == '-' or (prompt is None and stdin_content):
        # Reading from pipe as main input
        if not stdin_content:
            # Handle empty input
            click.echo("Error: No input provided", err=True)
            sys.exit(1)
            
        # Try to parse as JSON first
        try:
            import json
            json_input = json.loads(stdin_content)
            
            # Extract prompt from various possible fields
            prompt = (json_input.get('prompt') or 
                     json_input.get('query') or 
                     json_input.get('message') or 
                     json_input.get('text') or 
                     json_input.get('content'))
            
            if not prompt:
                # If no recognized prompt field, treat entire JSON as prompt
                prompt = stdin_content
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
            prompt = stdin_content
    elif prompt and stdin_content:
        # We have both a prompt and piped input - combine them
        prompt = f"{prompt}\n\nInput data:\n{stdin_content}"
            
    elif prompt is None:
        # If we got here without a prompt and not from stdin, something's wrong
        if allow_empty:
            return
        click.echo("Error: Missing argument 'prompt'", err=True)
        sys.exit(1)
    
    
    # Parse tools
    tools_list = None
    if tools:
        if tools == "all":
            # Enable all tools - pass None to let the backend decide
            tools_list = None
        else:
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
        aliases = config.get("models", {}).get("aliases", {})
        
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
        
        # Show aliases
        console.print()
        console.print("[bold green]Model Aliases:[/bold green]")
        for alias, model in sorted(aliases.items()):
            console.print(f"  • @{alias} → {model}")
                    
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


@main.command(name='ask', hidden=True)
@click.argument('prompt', nargs=-1, required=True)
@click.pass_context  
def ask_cmd(ctx, prompt):
    """Direct AI prompt (hidden default command)."""
    prompt_text = " ".join(prompt)
    
    # Get parent context for options
    parent_ctx = ctx.parent
    
    # Resolve model alias
    model = parent_ctx.params.get('model')
    if model:
        model = resolve_model_alias(model)
    
    ask_command(prompt_text,
                model,
                parent_ctx.params.get('system'), 
                parent_ctx.params.get('temperature'),
                parent_ctx.params.get('max_tokens'),
                parent_ctx.params.get('tools'),
                parent_ctx.params.get('stream'),
                parent_ctx.params.get('verbose'),
                parent_ctx.params.get('code'),
                parent_ctx.params.get('json_output'),
                allow_empty=False)


# Make 'ask' the default command if no subcommand is specified
main.add_command(ask_cmd, name='ask')


def cli_entry():
    """Entry point that handles both subcommands and direct prompts."""
    import sys
    
    # Check if we need to add 'ask' for direct prompt usage
    if len(sys.argv) > 1:
        # Get list of available commands dynamically
        available_commands = list(main.commands.keys())
        
        # Special case: ttt @model "prompt" -> ttt -m @model ask "prompt"
        if sys.argv[1].startswith('@'):
            if len(sys.argv) > 2:
                # Transform: ['ttt', '@model', 'prompt'] -> ['ttt', '-m', '@model', 'ask', 'prompt']
                model_alias = sys.argv[1]
                sys.argv[1:2] = ['-m', model_alias, 'ask']
                # Now it will be: ttt -m @model ask "prompt"
            else:
                # Just "ttt @model" - show help
                sys.argv[1:1] = ['--help']
        else:
            # Find the first non-option argument
            first_non_option_idx = None
            skip_next = False
            for i, arg in enumerate(sys.argv[1:], 1):
                if skip_next:
                    skip_next = False
                    continue
                if arg.startswith('-'):
                    # This is an option, check if it takes a value
                    if arg in ['-m', '--model', '-s', '--system', '-t', '--temperature', '--max-tokens', '--tools']:
                        skip_next = True
                else:
                    # This is the first non-option argument
                    first_non_option_idx = i
                    break
            
            # If we found a non-option arg that's not a known command, insert 'ask'
            if first_non_option_idx and sys.argv[first_non_option_idx] not in available_commands:
                sys.argv.insert(first_non_option_idx, 'ask')
    
    # Run the main CLI
    main()


if __name__ == "__main__":
    cli_entry()