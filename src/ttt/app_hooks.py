#!/usr/bin/env python3
"""Business logic hooks for the TTT CLI."""

import json as json_module
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import rich_click as click
from rich.console import Console

# Import required TTT modules
import ttt
from ttt.config.manager import ConfigManager
from ttt.core.api import ask as ttt_ask
from ttt.core.api import stream as ttt_stream
from ttt.session.manager import ChatSessionManager

# Initialize console
console = Console()

# Import helper functions we'll need
def setup_logging_level(
    verbose: bool = False, debug: bool = False, json_output: bool = False
) -> None:
    """Setup logging level based on verbosity flags."""
    import asyncio
    import logging

    from rich.logging import RichHandler

    if json_output:
        level = logging.WARNING
        logging.getLogger().handlers = []
        logging.getLogger().setLevel(level)
    elif debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    if not json_output and not logging.getLogger().handlers:
        console = Console()
        logging.basicConfig(
            level=level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(console=console, rich_tracebacks=True)],
        )
    elif not json_output:
        logging.getLogger().setLevel(level)

    if not debug:
        logging.getLogger("litellm").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.CRITICAL)

        def custom_exception_handler(loop: Any, context: Dict[str, Any]) -> None:
            exception = context.get("exception")
            if exception:
                if "Task was destroyed but it is pending" in str(exception):
                    return
                if verbose or debug:
                    loop.default_exception_handler(context)

        try:
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(custom_exception_handler)
        except RuntimeError:
            pass


def resolve_model_alias(model: str) -> str:
    """Resolve model alias to full model name."""
    if model and model.startswith("@"):
        alias = model[1:]
        try:
            config_manager = ConfigManager()
            merged_config = config_manager.get_merged_config()
            aliases = merged_config.get("models", {}).get("aliases", {})
            if alias in aliases:
                return str(aliases[alias])

            available_models = merged_config.get("models", {}).get("available", {})
            for model_name, model_info in available_models.items():
                if isinstance(model_info, dict):
                    model_aliases = model_info.get("aliases", [])
                    if alias in model_aliases:
                        return str(model_name)

            console.print(
                f"[yellow]Warning: Unknown model alias '@{alias}', using '{alias}'[/yellow]"
            )
            return alias
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not resolve model alias: {e}[/yellow]"
            )
            return alias

    if model and not model.startswith("openrouter/"):
        has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        has_google = bool(os.getenv("GOOGLE_API_KEY"))

        if has_openrouter and not (has_openai or has_anthropic or has_google):
            openrouter_mappings = {
                "gpt-4o": "openrouter/openai/gpt-4o",
                "gpt-4o-mini": "openrouter/openai/gpt-4o-mini",
                "gpt-4": "openrouter/openai/gpt-4",
                "gpt-3.5-turbo": "openrouter/openai/gpt-3.5-turbo",
                "claude-3-5-sonnet-20241022": "openrouter/anthropic/claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022": "openrouter/anthropic/claude-3-5-haiku-20241022",
                "gemini-1.5-pro": "openrouter/google/gemini-1.5-pro",
                "gemini-1.5-flash": "openrouter/google/gemini-1.5-flash",
            }

            if model in openrouter_mappings:
                console.print(f"[dim]Routing {model} through OpenRouter...[/dim]")
                return openrouter_mappings[model]

    return model


def parse_tools_arg(tools: Optional[str]) -> Optional[str]:
    """Parse tools argument and expand categories."""
    if tools is None:
        return None

    if tools == "":
        return "all"

    from ttt.tools.builtins import TOOL_CATEGORIES

    expanded_tools = []
    for item in tools.split(","):
        item = item.strip()
        if item in TOOL_CATEGORIES:
            category_tools = TOOL_CATEGORIES[item]
            expanded_tools.extend(category_tools)
        else:
            expanded_tools.append(item)

    return ",".join(expanded_tools) if expanded_tools else tools


def resolve_tools(tool_specs: List[str]) -> List[Any]:
    """Resolve tool specifications to actual tool functions."""
    tools: List[Any] = []

    try:
        from ttt.tools import get_tool, list_tools

        for spec in tool_specs:
            if ":" in spec:
                category, tool_name = spec.split(":", 1)
                tool_list = list_tools(category=category)
                found_tool = None
                for tool_def in tool_list:
                    if tool_def.name == tool_name:
                        found_tool = tool_def.function
                        break
                if found_tool:
                    tools.append(found_tool)
                else:
                    console.print(
                        f"[yellow]Warning: Tool {tool_name} not found in category {category}[/yellow]"
                    )
            else:
                found_tool_def = get_tool(spec)
                if found_tool_def:
                    tools.append(found_tool_def.function)
                else:
                    console.print(f"[yellow]Warning: Tool {spec} not found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error resolving tools: {e}[/red]")

    return tools


def apply_coding_optimization(kwargs: Dict[str, Any]) -> None:
    """Apply optimizations for coding requests."""
    if "model" not in kwargs:
        default_coding_model = os.getenv("TTT_CODING_MODEL", "@coding")
        kwargs["model"] = resolve_model_alias(default_coding_model)

    if "temperature" not in kwargs:
        kwargs["temperature"] = 0.1

    if "system" not in kwargs:
        kwargs["system"] = (
            "You are an expert programmer. Provide clean, well-documented code "
            "with clear explanations. Follow best practices and consider edge cases."
        )


# Main hook functions

def on_ask(prompt: Tuple[str, ...], model: Optional[str], temperature: float,
           max_tokens: Optional[int], tools: bool, session: Optional[str], system: Optional[str], stream: bool, json: bool) -> None:
    """Hook for 'ask' command."""
    # Parse provider shortcuts from prompt arguments
    prompt_list = list(prompt) if prompt else []

    # Check if first argument is a provider shortcut
    if prompt_list and prompt_list[0].startswith('@') and not model:
        potential_model = prompt_list[0]
        # Remove the @ prefix to get the alias
        model_alias = potential_model[1:]

        # Resolve the alias and set as model if valid
        resolved_model = resolve_model_alias(f"@{model_alias}")
        if resolved_model != f"@{model_alias}":  # If resolve_model_alias changed it, it's valid
            model = resolved_model
            prompt_list = prompt_list[1:]  # Remove the @provider from prompt
        # If not a valid alias, leave it as part of the prompt

    # Join remaining prompt tuple into a single string
    prompt_text = " ".join(prompt_list) if prompt_list else None

    # Setup logging
    setup_logging_level(json_output=json)

    # Handle missing prompt
    if prompt_text is None and sys.stdin.isatty():
        click.echo("Error: Missing argument 'prompt'", err=True)
        sys.exit(1)

    # Handle stdin input
    stdin_content = None
    if not sys.stdin.isatty():
        try:
            stdin_content = sys.stdin.read().strip()
        except EOFError:
            stdin_content = ""

    if prompt_text == "-" or (prompt_text is None and stdin_content):
        if not stdin_content:
            click.echo("Error: No input provided", err=True)
            sys.exit(1)

        try:
            json_input = json_module.loads(stdin_content)
            prompt_text = (
                json_input.get("prompt")
                or json_input.get("query")
                or json_input.get("message")
                or json_input.get("text")
                or json_input.get("content")
            )

            if not prompt_text:
                prompt_text = stdin_content
            else:
                if not model and json_input.get("model"):
                    model = json_input.get("model")
                if temperature is None and json_input.get("temperature") is not None:
                    temperature = json_input.get("temperature")
                if not max_tokens and json_input.get("max_tokens"):
                    max_tokens = json_input.get("max_tokens")
        except json_module.JSONDecodeError:
            prompt_text = stdin_content
    elif prompt_text and stdin_content:
        prompt_text = f"{prompt_text}\n\nInput data:\n{stdin_content}"

    elif prompt_text is None:
        click.echo("Error: Missing argument 'prompt'", err=True)
        sys.exit(1)

    # Resolve model alias
    if model:
        model = resolve_model_alias(model)

    # Build request parameters
    kwargs: Dict[str, Any] = {}
    if model:
        kwargs["model"] = model
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    if tools:
        kwargs["tools"] = None  # Enable all tools
    if session:
        kwargs["session_id"] = session
    if system:
        kwargs["system"] = system

    try:
        if json:
            # JSON output mode - collect response and format as JSON
            response = ttt_ask(prompt_text, **kwargs)
            output = {
                "response": str(response).strip(),
                "model": kwargs.get("model"),
                "temperature": kwargs.get("temperature"),
                "max_tokens": kwargs.get("max_tokens"),
                "tools_enabled": kwargs.get("tools") is not None,
                "session_id": kwargs.get("session_id"),
                "system": kwargs.get("system")
            }
            click.echo(json_module.dumps(output, indent=2))
        elif stream:
            chunks = list(ttt_stream(prompt_text, **kwargs))
            for i, chunk in enumerate(chunks):
                if i == len(chunks) - 1:  # Last chunk
                    click.echo(chunk.rstrip('\n'), nl=False)
                else:
                    click.echo(chunk, nl=False)
            click.echo()  # Always add exactly one newline at the end
        else:
            response = ttt_ask(prompt_text, **kwargs)
            click.echo(str(response).strip())
    except Exception as e:
        if json:
            error_output = {
                "error": str(e),
                "model": kwargs.get("model"),
                "parameters": kwargs
            }
            click.echo(json_module.dumps(error_output, indent=2), err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def on_chat(model: Optional[str], session: Optional[str], tools: bool, markdown: bool) -> None:
    """Hook for 'chat' command."""
    from ttt.session.manager import ChatSessionManager

    # Setup logging
    setup_logging_level()

    # Initialize session manager
    session_manager = ChatSessionManager()

    # Resolve model alias if provided
    if model:
        model = resolve_model_alias(model)

    # Parse tools
    parsed_tools: Optional[List[str]] = None
    if tools:
        parsed_tools = None  # Enable all tools

    # Load or create session
    if session:
        chat_session = session_manager.load_session(session)
        if not chat_session:
            console.print(f"[yellow]Session '{session}' not found. Creating new session.[/yellow]")
            chat_session = session_manager.create_session(
                session_id=session, model=model, tools=parsed_tools
            )
    else:
        chat_session = session_manager.create_session(
            model=model, tools=parsed_tools
        )

    # Build kwargs for chat session
    chat_kwargs: Dict[str, Any] = {}
    if chat_session.model:
        chat_kwargs["model"] = chat_session.model
    if chat_session.system_prompt:
        chat_kwargs["system"] = chat_session.system_prompt
    if chat_session.tools:
        chat_kwargs["tools"] = resolve_tools(chat_session.tools)
    chat_kwargs["stream"] = True

    # Create chat session with context from previous messages
    messages: List[Dict[str, str]] = []
    if chat_session.system_prompt:
        messages.append({"role": "system", "content": chat_session.system_prompt})
    for msg in chat_session.messages:
        messages.append({"role": msg.role, "content": msg.content})

    # Start chat loop
    try:
        # Use the chat API
        with ttt.chat(**chat_kwargs) as api_chat_session:
            # Restore message history
            if messages:
                api_chat_session.history = messages

            console.print("[bold blue]AI Chat Session[/bold blue]")
            if chat_session.model:
                console.print(f"Model: {chat_session.model}")
            if chat_session.system_prompt:
                console.print(f"System: {chat_session.system_prompt[:50]}...")
            console.print("Type /exit to quit, /clear to clear history, /help for commands")
            console.print()

            # Show previous messages if any
            if chat_session.messages:
                console.print("[dim]--- Previous conversation ---[/dim]")
                for msg in chat_session.messages[-10:]:  # Show last 10 messages
                    if msg.role == "user":
                        console.print(f"[bold cyan]You:[/bold cyan] {msg.content}")
                    else:
                        console.print(f"[bold green]AI:[/bold green] {msg.content}")
                console.print("[dim]--- Continue conversation ---[/dim]")
                console.print()

            while True:
                try:
                    user_input = click.prompt("You", type=str, prompt_suffix=": ")
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
                        chat_session.messages = []
                        session_manager.save_session(chat_session)
                        console.print("[yellow]Chat history cleared.[/yellow]")
                        # Reset chat session messages
                        api_chat_session.history = (
                            [{"role": "system", "content": chat_session.system_prompt}]
                            if chat_session.system_prompt
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
                session_manager.add_message(chat_session, "user", user_input)

                try:
                    # Get AI response
                    response = api_chat_session.ask(user_input)

                    # Display response
                    console.print(f"[bold green]AI:[/bold green] {response}")

                    # Add AI response to session
                    session_manager.add_message(
                        chat_session,
                        "assistant",
                        str(response),
                        model=response.model if hasattr(response, "model") else None,
                    )

                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")

    except (EOFError, KeyboardInterrupt):
        # Normal exit, don't show error
        pass
    except Exception as e:
        # Only show error if it's not an empty exception
        if str(e).strip():
            console.print(f"[red]Error starting chat session: {e}[/red]")


def on_list(resource: str, format: str, verbose: bool) -> None:
    """Hook for 'list' command."""
    if resource == 'models':
        show_models_list(json_output=(format == 'json'))
    elif resource == 'sessions':
        session_manager = ChatSessionManager()
        if format == 'json':
            sessions = session_manager.list_sessions()
            click.echo(json_module.dumps(sessions))
        else:
            session_manager.display_sessions_table()
    elif resource == 'tools':
        from ttt.tools import list_tools
        tools = list_tools()
        if format == 'json':
            tools_data = [{"name": t.name, "description": t.description} for t in tools]
            click.echo(json_module.dumps(tools_data))
        else:
            console.print("\n[bold]Available Tools:[/bold]")
            for tool in tools:
                console.print(f"  • [cyan]{tool.name}[/cyan]: {tool.description}")


def on_config_get(key: str) -> None:
    """Hook for 'config get' subcommand."""
    config_manager = ConfigManager()
    config_manager.show_value(key)


def on_config_set(key: str, value: str) -> None:
    """Hook for 'config set' subcommand."""
    config_manager = ConfigManager()
    config_manager.set_value(key, value)


def on_config_list(show_secrets: bool) -> None:
    """Hook for 'config list' subcommand."""
    config_manager = ConfigManager()
    merged_config = config_manager.get_merged_config()

    # Mask sensitive values unless show_secrets is True
    if not show_secrets:
        def mask_sensitive(obj: Any, key: Optional[str] = None) -> Any:
            if isinstance(obj, dict):
                return {k: mask_sensitive(v, k) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [mask_sensitive(item) for item in obj]
            elif key and ('key' in key.lower() or 'secret' in key.lower() or 'token' in key.lower()):
                return "***" if obj else None
            else:
                return obj

        merged_config = mask_sensitive(merged_config)

    click.echo(json_module.dumps(merged_config, indent=2))


def on_export(session: str, format: str, output: Optional[str], include_metadata: bool) -> None:
    """Hook for 'export' command."""
    session_manager = ChatSessionManager()

    # Load session
    chat_session = session_manager.load_session(session)
    if not chat_session:
        click.echo(f"Error: Session '{session}' not found", err=True)
        sys.exit(1)

    # Export data
    export_data = {
        "session_id": chat_session.id,
        "created_at": chat_session.created_at.isoformat() if hasattr(chat_session, 'created_at') else None,
        "messages": chat_session.messages
    }

    if include_metadata:
        export_data["metadata"] = {
            "model": getattr(chat_session, 'model', None),
            "system_prompt": getattr(chat_session, 'system_prompt', None),
            "tools": getattr(chat_session, 'tools', None),
        }

    # Format output
    if format == 'json':
        output_text = json_module.dumps(export_data, indent=2)
    elif format == 'yaml':
        try:
            import yaml
            output_text = yaml.dump(export_data, default_flow_style=False)
        except ImportError:
            click.echo("Error: PyYAML is not installed. Use 'pip install pyyaml'", err=True)
            sys.exit(1)
    else:  # markdown
        output_text = f"# Chat Session: {session}\n\n"
        if include_metadata:
            output_text += f"**Model**: {export_data['metadata']['model']}\n\n"

        for msg in export_data['messages']:
            output_text += f"## {msg['role'].capitalize()}\n\n{msg['content']}\n\n"

    # Write output
    if output:
        Path(output).write_text(output_text)
        click.echo(f"Session exported to {output}")
    else:
        click.echo(output_text)


def on_tools_enable(tool_name: str) -> None:
    """Hook for 'tools enable' subcommand."""
    config_manager = ConfigManager()
    merged_config = config_manager.get_merged_config()
    disabled_tools = merged_config.get("tools", {}).get("disabled", [])

    if tool_name in disabled_tools:
        disabled_tools.remove(tool_name)
        config_manager.set_value("tools.disabled", disabled_tools)
        click.echo(f"Tool '{tool_name}' has been enabled")
    else:
        click.echo(f"Tool '{tool_name}' is already enabled")


def on_tools_disable(tool_name: str) -> None:
    """Hook for 'tools disable' subcommand."""
    config_manager = ConfigManager()
    merged_config = config_manager.get_merged_config()
    disabled_tools = merged_config.get("tools", {}).get("disabled", [])

    if tool_name not in disabled_tools:
        disabled_tools.append(tool_name)
        config_manager.set_value("tools.disabled", disabled_tools)
        click.echo(f"Tool '{tool_name}' has been disabled")
    else:
        click.echo(f"Tool '{tool_name}' is already disabled")


def on_tools_list(show_disabled: bool) -> None:
    """Hook for 'tools list' subcommand."""
    from ttt.tools import list_tools

    config_manager = ConfigManager()
    merged_config = config_manager.get_merged_config()
    disabled_tools = merged_config.get("tools", {}).get("disabled", [])

    tools = list_tools()

    console.print("\n[bold]Available Tools:[/bold]")
    for tool in tools:
        status = "[red]disabled[/red]" if tool.name in disabled_tools else "[green]enabled[/green]"
        if show_disabled or tool.name not in disabled_tools:
            console.print(f"  • [cyan]{tool.name}[/cyan] ({status}): {tool.description}")


# Additional helper functions needed by hooks

def show_models_list(json_output: bool = False) -> None:
    """Show list of available models."""
    from ttt.config.schema import get_model_registry

    try:
        model_registry = get_model_registry()
        model_names = model_registry.list_models()
        models = [model_registry.get_model(name) for name in model_names if model_registry.get_model(name)]

        if json_output:
            models_data = []
            for model in models:
                model_data = {
                    "name": model.name,
                    "provider": model.provider,
                    "provider_name": model.provider_name,
                    "context_length": model.context_length,
                    "cost_per_token": model.cost_per_token,
                    "speed": model.speed,
                    "quality": model.quality,
                    "aliases": model.aliases,
                }
                models_data.append(model_data)
            click.echo(json_module.dumps(models_data))
        else:
            from rich.table import Table

            table = Table(title="Available Models")
            table.add_column("Model Name", style="cyan")
            table.add_column("Provider", style="magenta")
            table.add_column("Speed", style="green")
            table.add_column("Quality", style="yellow")
            table.add_column("Context", style="blue")

            for model in models:
                context_str = f"{model.context_length:,}" if model.context_length else "N/A"
                table.add_row(
                    model.name,
                    model.provider,
                    model.speed,
                    model.quality,
                    context_str,
                )

            console.print(table)
    except Exception as e:
        if json_output:
            error_output = {"error": str(e)}
            click.echo(json_module.dumps(error_output))
        else:
            console.print(f"[red]Error listing models: {e}[/red]")


def show_model_info(model_name: str, json_output: bool = False) -> None:
    """Show detailed information about a specific model."""
    from ttt.config.schema import get_model_registry

    try:
        model_registry = get_model_registry()
        model = model_registry.get_model(model_name)

        if not model:
            raise ValueError(f"Model '{model_name}' not found")

        if json_output:
            model_data = {
                "name": model.name,
                "provider": model.provider,
                "provider_name": model.provider_name,
                "context_length": model.context_length,
                "cost_per_token": model.cost_per_token,
                "speed": model.speed,
                "quality": model.quality,
                "aliases": model.aliases,
                "capabilities": model.capabilities,
            }
            click.echo(json_module.dumps(model_data))
        else:
            console.print(f"\n[bold]Model Information: {model.name}[/bold]")
            console.print(f"Provider: {model.provider}")
            console.print(f"Provider Name: {model.provider_name}")
            console.print(f"Speed: {model.speed}")
            console.print(f"Quality: {model.quality}")

            if model.context_length:
                console.print(f"Context Length: {model.context_length:,} tokens")

            if model.cost_per_token:
                console.print(f"Cost per Token: ${model.cost_per_token:.6f}")

            if model.aliases:
                console.print(f"Aliases: {', '.join(model.aliases)}")

            if model.capabilities:
                console.print(f"Capabilities: {', '.join(model.capabilities)}")
    except Exception as e:
        if json_output:
            error_output = {"error": str(e)}
            click.echo(json_module.dumps(error_output))
        else:
            console.print(f"[red]Error getting model info: {e}[/red]")


def show_backend_status(json_output: bool = False) -> None:
    """Show backend status."""
    status_data: Dict[str, Any] = {"backends": {}}

    # Check local backend
    try:
        import ttt.backends.local as local_module
        local = local_module.LocalBackend()
        local_status = {
            "available": local.is_available,
            "type": "local",
            "url": local.base_url,
        }
        if local_status["available"]:
            try:
                models = local.list_models()
                local_status["models"] = len(models)
            except Exception:
                local_status["models"] = 0
        status_data["backends"]["local"] = local_status
    except Exception as e:
        status_data["backends"]["local"] = {
            "available": False,
            "error": str(e),
        }

    # Check cloud backend
    try:

        # Check API keys
        api_keys = {
            "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "google": bool(os.getenv("GOOGLE_API_KEY")),
        }

        cloud_status = {
            "available": any(api_keys.values()),
            "type": "cloud",
            "api_keys": api_keys,
        }
        status_data["backends"]["cloud"] = cloud_status
    except Exception as e:
        status_data["backends"]["cloud"] = {
            "available": False,
            "error": str(e),
        }

    # Add overall status
    status_data["healthy"] = any(
        backend.get("available", False) for backend in status_data["backends"].values()
    )

    if json_output:
        click.echo(json_module.dumps(status_data))
    else:
        console.print("\n[bold]TTT System Status[/bold]\n")

        # Local backend
        local_status = status_data["backends"]["local"]
        if local_status["available"]:
            console.print("✅ Local Backend (Ollama): [green]Available[/green]")
            console.print(f"   URL: {local_status['url']}")
            console.print(f"   Models: {local_status.get('models', 0)}")
        else:
            console.print("❌ Local Backend (Ollama): [red]Not Available[/red]")
            if "error" in local_status:
                console.print(f"   Error: {local_status['error']}")

        console.print()

        # Cloud backend
        cloud_status = status_data["backends"]["cloud"]
        if cloud_status["available"]:
            console.print("✅ Cloud Backend: [green]Available[/green]")
            console.print("   API Keys:")
            for provider, has_key in cloud_status["api_keys"].items():
                status = "[green]✓[/green]" if has_key else "[red]✗[/red]"
                console.print(f"     {status} {provider}")
        else:
            console.print("❌ Cloud Backend: [red]Not Available[/red]")
            if "error" in cloud_status:
                console.print(f"   Error: {cloud_status['error']}")

        console.print()

        # Overall status
        if status_data["healthy"]:
            console.print("🎉 [bold green]System is ready to use![/bold green]")
        else:
            console.print("⚠️  [bold yellow]No backends available. Please configure API keys or install Ollama.[/bold yellow]")


# Add hook functions for missing commands that need to be added to CLI
def on_status(json: bool) -> None:
    """Hook for 'status' command."""
    show_backend_status(json_output=json)


def on_models(json: bool) -> None:
    """Hook for 'models' command."""
    show_models_list(json_output=json)


def on_info(model: str, json: bool) -> None:
    """Hook for 'info' command."""
    show_model_info(model, json_output=json)
