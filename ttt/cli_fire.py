#!/usr/bin/env python3
"""Fire-based CLI for the AI library with simplified argument handling."""

import io
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set environment variable BEFORE any imports if JSON mode is detected
if "--json" in sys.argv:
    os.environ["TTT_JSON_MODE"] = "true"

import fire
from dotenv import load_dotenv
from rich.console import Console

# Don't import ttt at module level - defer all imports to avoid early config loading
# This will be handled inside main() or individual methods

# Defer imports to avoid triggering config loading during module import
# These will be imported inside the methods that need them

# Suppress the common aiohttp warning about pending tasks being destroyed
warnings.filterwarnings(
    "ignore", message="Task was destroyed but it is pending!", category=RuntimeWarning
)

# Also suppress via environment variable for asyncio
os.environ.setdefault("PYTHONWARNINGS", "ignore::RuntimeWarning")

# Load environment variables from .env file (same logic as original)
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
try:
    import ttt

    if hasattr(ttt, "__file__"):
        package_dir = Path(ttt.__file__).parent
        project_root = package_dir.parent
        env_paths.append(project_root / ".env")
        env_paths.append(project_root.parent / ".env")
except Exception:
    pass

# 4. Common locations
env_paths.extend(
    [
        Path.home() / ".env",
    ]
)

# Load the first .env file found
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        if os.getenv("TTT_DEBUG"):
            print(f"Loaded .env from: {env_path}")
        break

console = Console()


class TTT:
    """Fire-based CLI for TTT - Transform any text with intelligent AI processing"""

    def __init__(self) -> None:
        """Initialize TTT CLI."""
        pass

    def __call__(
        self,
        *args: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[str] = None,
        stream: bool = False,
        verbose: bool = False,
        debug: bool = False,
        code: bool = False,
        json: bool = False,
    ) -> None:
        """Main prompt handler - supports @model syntax and flexible flags.

        Args:
            *args: The prompt text as positional arguments
            model: AI model to use (e.g., @claude, @gpt4, gpt-4o)
            system: Define AI behavior and expertise with custom instructions
            temperature: Balance creativity vs precision (0=focused, 1=creative)
            max_tokens: Control response length for concise or detailed output
            tools: Enable AI tools (empty=all, or specify: web,code)
            stream: Watch responses appear in real-time as AI thinks
            verbose: Show detailed processing information and diagnostics
            debug: Enable comprehensive debugging for troubleshooting
            code: Optimize AI responses for programming and development tasks
            json: Export results as JSON for automation and scripting
        """
        # Setup logging based on verbosity
        from ttt.cli import setup_logging_level

        setup_logging_level(verbose, debug, json)

        # Handle @model syntax (simple 3-line conversion)
        if args and args[0].startswith("@"):
            model = args[0]  # Will be resolved by resolve_model_alias
            prompt = " ".join(args[1:])
        else:
            prompt = " ".join(args)

        # If no prompt, check for piped input or show help
        if not prompt or not prompt.strip():
            if sys.stdin.isatty():
                # Interactive terminal - show help
                print(self._get_help())
                return
            else:
                # Check for piped input with timeout
                import select

                try:
                    if not select.select([sys.stdin], [], [], 30)[0]:
                        print(self._get_help())
                        return
                    else:
                        # Read stdin content
                        stdin_content = sys.stdin.read().strip()
                        if stdin_content:
                            prompt = stdin_content
                        else:
                            print(self._get_help())
                            return
                except (OSError, io.UnsupportedOperation):
                    print(self._get_help())
                    return

        # Import locally to avoid early config loading
        from ttt.cli import ask_command, parse_tools_arg, resolve_model_alias

        # Resolve model alias
        if model:
            model = resolve_model_alias(model)
        import ttt.cli

        # Set up early warnings for JSON mode
        early_warnings = []
        if json:
            cwd = os.getcwd()
            config_path = os.path.join(cwd, "config.yaml")
            if not os.path.exists(config_path):
                early_warnings.append(
                    "Project config.yaml not found, using minimal defaults"
                )
        ttt.cli.early_warnings = early_warnings

        # Parse tools argument
        tools = parse_tools_arg(tools)

        # Call existing ask_command logic
        ask_command(
            prompt,
            model,
            system,
            temperature,
            max_tokens,
            tools,
            stream,
            verbose,
            code,
            json,
            allow_empty=False,
        )

    def version(self) -> None:
        """Show version and system information."""
        from ttt.cli import get_ttt_version

        pkg_version = get_ttt_version()
        print(f"TTT Library v{pkg_version}")

    def status(self, json: bool = False) -> None:
        """Verify system health and API connectivity."""
        from ttt.cli import show_backend_status

        show_backend_status(json)

    def models(self, json: bool = False) -> None:
        """Browse all available AI models and their capabilities."""
        from ttt.cli import show_models_list

        show_models_list(json)

    def config(
        self,
        action: Optional[str] = None,
        key: Optional[str] = None,
        value: Optional[str] = None,
        reset: bool = False,
        json: bool = False,
    ) -> None:
        """Access configuration management and preferences.

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
            # Note: Fire doesn't have click.confirm, so we'll assume yes for now
            # In real usage, user would have typed --reset explicitly
            config_manager.reset_config()
            return

        # Handle different actions
        if not action:
            # No action specified - show all config
            if json:
                import json as json_lib

                config = config_manager.get_merged_config()
                print(json_lib.dumps(config, indent=2))
            else:
                config_manager.display_config()
        elif action == "get" and key:
            # Get specific value
            if json:
                import json as json_lib

                config = config_manager.get_merged_config()
                # Navigate to the key
                config_value: Any = config
                for part in key.split("."):
                    if isinstance(config_value, dict) and part in config_value:
                        config_value = config_value[part]
                    else:
                        config_value = None
                        break
                print(json_lib.dumps({key: config_value}, indent=2))
            else:
                config_manager.show_value(key)
        elif action == "set" and key and value:
            # Set specific value
            config_manager.set_value(key, value)
            if json:
                import json as json_lib

                print(json_lib.dumps({"status": "success", "key": key, "value": value}))
        elif action == "set" and key and not value:
            # Special case: missing value for set command
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
                console.print(
                    "  ttt config                          # Show all configuration"
                )
                console.print(
                    "  ttt config get KEY                  # Show specific value"
                )
                console.print("  ttt config set KEY VALUE            # Set a value")
                console.print(
                    "  ttt config set alias.NAME MODEL     # Set a model alias"
                )
                console.print(
                    "  ttt config --reset                  # Reset to defaults"
                )

    def chat(
        self,
        resume: bool = False,
        session_id: Optional[str] = None,
        list_sessions: bool = False,
        model: Optional[str] = None,
        system: Optional[str] = None,
        tools: Optional[str] = None,
    ) -> None:
        """Launch interactive conversation mode with memory.

        Args:
            resume: Continue the last chat session
            session_id: Use a named chat session (--id)
            list_sessions: Show all chat sessions (--list)
            model: Select AI model (overrides default)
            system: Set system prompt for the session
            tools: Enable tools for this session
        """
        from ttt.chat_sessions import ChatSessionManager

        # Initialize session manager
        session_manager = ChatSessionManager()

        # Handle --list
        if list_sessions:
            session_manager.display_sessions_table()
            return

        # Resolve model alias if provided
        if model:
            from ttt.cli import resolve_model_alias

            model = resolve_model_alias(model)

        # Parse tools
        parsed_tools: Optional[List[str]] = None
        if tools:
            from ttt.cli import parse_tools_arg

            parsed_tools_str = parse_tools_arg(tools)
            if parsed_tools_str == "all":
                parsed_tools = None  # Will enable all tools
            elif parsed_tools_str:
                parsed_tools = [t.strip() for t in parsed_tools_str.split(",")]

        # Load or create session
        if resume:
            session = session_manager.load_last_session()
            if not session:
                console.print(
                    "[yellow]No previous session found. Starting new session.[/yellow]"
                )
                session = session_manager.create_session(
                    model=model, system_prompt=system, tools=parsed_tools
                )
            else:
                console.print(f"[green]Resuming session: {session.id}[/green]")
                # Override settings if provided
                if model:
                    session.model = model
                if system:
                    session.system_prompt = system
                if parsed_tools is not None:
                    session.tools = parsed_tools
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
            if parsed_tools is not None:
                session.tools = parsed_tools
        else:
            # Create new session
            session = session_manager.create_session(
                model=model, system_prompt=system, tools=parsed_tools
            )
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
        chat_kwargs: Dict[str, Any] = {}
        if session.model:
            chat_kwargs["model"] = session.model
        if session.system_prompt:
            chat_kwargs["system"] = session.system_prompt
        if session.tools:
            from ttt.cli import resolve_tools

            chat_kwargs["tools"] = resolve_tools(session.tools)

        # Create chat session with context from previous messages
        messages: List[Dict[str, str]] = []
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
                    chat_session.history = messages

                while True:
                    try:
                        user_input = input("You: ")
                    except (EOFError, KeyboardInterrupt):
                        console.print("\n[yellow]Chat session ended.[/yellow]")
                        break

                    if not user_input.strip():
                        continue

                    # Handle chat commands
                    if user_input.startswith("/"):
                        if user_input in ["/exit", "/quit"]:
                            console.print("[yellow]Chat session ended.[/yellow]")
                            break
                        elif user_input == "/clear":
                            session.messages = []
                            session_manager.save_session(session)
                            console.print("[yellow]Chat history cleared.[/yellow]")
                            # Reset chat session messages
                            chat_session.history = (
                                [{"role": "system", "content": session.system_prompt}]
                                if session.system_prompt
                                else []
                            )
                            continue
                        elif user_input == "/help":
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
                        session_manager.add_message(
                            session,
                            "assistant",
                            str(response),
                            model=(
                                response.model if hasattr(response, "model") else None
                            ),
                        )

                    except Exception as e:
                        console.print(f"[red]Error: {e}[/red]")

        except Exception as e:
            console.print(f"[red]Error starting chat session: {e}[/red]")

    def _get_help(self) -> str:
        """Generate help text."""
        from ttt.cli import get_ttt_version

        return f"""🚀 TTT {get_ttt_version()} - Transform any text with intelligent AI processing

TTT empowers developers, writers, and creators to process text with precision.
From simple transformations to complex analysis - AI-powered and pipeline-ready.

💡 Quick Examples:
  ttt "Fix grammar in this text"           # Instant text cleanup
  ttt @claude "Summarize this article"     # Use Claude model
  echo "data.txt" | ttt "Convert to JSON"  # Pipeline integration
  ttt chat                                 # Interactive AI conversation

🎯 Commands:
  chat     💬 Launch interactive conversation mode
  status   ⚡ Verify system health and API connectivity
  models   🤖 Browse available AI models
  config   ⚙️  Manage configuration settings
  version  📋 Show version information

🔧 Options:
  --model, -m      🤖 Select your AI model (e.g., @claude, @gpt4, gpt-4o)
  --system, -s     🎭 Define AI behavior and expertise
  --temperature, -t 🌡️  Balance creativity vs precision (0=focused, 1=creative)
  --max-tokens     📝 Control response length
  --tools          🔧 Enable AI tools (empty=all, or specify: web,code)
  --stream         ⚡ Watch responses appear in real-time
  --verbose, -v    🔍 Show detailed processing information
  --debug          🐛 Enable comprehensive debugging
  --code           💻 Optimize for programming tasks
  --json           📦 Export results as JSON

🔑 Quick Setup:
  export OPENROUTER_API_KEY=your-key-here
  ttt status  # Verify your installation
"""


def main() -> None:
    """Entry point for Fire CLI."""
    # Check for JSON mode BEFORE Fire processes anything
    if "--json" in sys.argv:
        import logging

        # Completely disable all logging output for JSON mode
        logging.disable(logging.CRITICAL)

        # Also redirect stderr to suppress any direct prints
        original_stderr = sys.stderr
        sys.stderr = io.StringIO()

        # Set environment variable for any code that checks it
        os.environ["TTT_JSON_MODE"] = "true"

        try:
            fire.Fire(TTT)
        finally:
            # Restore stderr and logging
            sys.stderr = original_stderr
            logging.disable(logging.NOTSET)
    else:
        fire.Fire(TTT)


if __name__ == "__main__":
    main()
