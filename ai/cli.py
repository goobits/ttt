#!/usr/bin/env python3
"""Modern Click-based CLI for the AI library."""

import sys
import os
from typing import Optional, List
import click
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

console = Console()

# Import AI library modules
import ai


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def main(ctx, version):
    """AI Library - Unified AI Interface for local and cloud models."""
    if version:
        click.echo(f"AI Library v{getattr(ai, '__version__', '0.4.0')}")
        return
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument('prompt', required=True)
@click.option('--model', '-m', help='Specific model to use')
@click.option('--system', '-s', help='System prompt to set context')
@click.option('--temperature', '-t', type=float, help='Sampling temperature (0-1)')
@click.option('--max-tokens', type=int, help='Maximum tokens to generate')
@click.option('--backend', '-b', type=click.Choice(['local', 'cloud', 'auto']), help='Backend to use')
@click.option('--fast', is_flag=True, help='Prefer speed over quality')
@click.option('--quality', is_flag=True, help='Prefer quality over speed')
@click.option('--tools', help='Comma-separated list of tools to enable')
@click.option('--stream', is_flag=True, help='Stream the response')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--offline', is_flag=True, help='Force local backend')
@click.option('--online', is_flag=True, help='Force cloud backend')
@click.option('--code', is_flag=True, help='Optimize for code-related tasks')
def ask(prompt, model, system, temperature, max_tokens, backend, fast, quality, 
        tools, stream, verbose, offline, online, code):
    """Ask the AI a question and get a response."""
    
    # Handle stdin input
    if prompt == '-':
        prompt = sys.stdin.read().strip()
        if not prompt:
            click.echo("Error: No input provided via stdin", err=True)
            sys.exit(1)
    
    # Handle shortcuts
    if offline:
        backend = 'local'
    elif online:
        backend = 'cloud'
    
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
    if backend:
        kwargs['backend'] = backend
    if fast:
        kwargs['fast'] = True
    if quality:
        kwargs['quality'] = True
    if tools_list:
        kwargs['tools'] = tools_list
    
    # Apply coding optimizations
    if code or is_coding_request(prompt):
        apply_coding_optimization(kwargs)
    
    try:
        if stream:
            # Stream response
            for chunk in ai.stream(prompt, **kwargs):
                click.echo(chunk, nl=False)
            click.echo()  # Final newline
        else:
            # Regular response
            response = ai.ask(prompt, **kwargs)
            click.echo(str(response))
            
            if verbose:
                click.echo(f"\nModel: {response.model}", err=True)
                click.echo(f"Backend: {response.backend}", err=True)
                click.echo(f"Time: {response.time:.2f}s", err=True)
                if hasattr(response, 'tokens_in') and response.tokens_in:
                    click.echo(f"Tokens: {response.tokens_in} in, {response.tokens_out} out", err=True)
                    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--model', '-m', help='Default model for the session')
@click.option('--system', '-s', help='System prompt for the session')
@click.option('--backend', '-b', type=click.Choice(['local', 'cloud', 'auto']), help='Backend to use')
@click.option('--session-id', help='Session ID for persistent chat')
@click.option('--tools', help='Comma-separated list of tools to enable')
@click.option('--load', help='Load chat session from file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def chat(model, system, backend, session_id, tools, load, verbose):
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
    if backend:
        kwargs['backend'] = backend
    if session_id:
        kwargs['session_id'] = session_id
    if tools_list:
        kwargs['tools'] = tools_list
    
    try:
        # Load existing session if requested
        if load:
            from ai.chat import PersistentChatSession
            session = PersistentChatSession.load(load)
            console.print(f"[green]Loaded session from {load}[/green]")
        else:
            session = ai.chat(**kwargs).__enter__()
        
        console.print("[bold blue]AI Chat Session[/bold blue]")
        console.print("Type /exit to quit, /save <filename> to save session, /clear to clear history")
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


@main.command(name='backend-status')
def backend_status():
    """Show the status of available backends."""
    show_backend_status()


@main.command(name='models-list')
def models_list():
    """List available models from all backends."""
    show_models_list()


@main.command(name='tools-list')
def tools_list():
    """List available tools."""
    show_tools_list()


# Helper functions
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
    console.print("[bold green]Cloud Models:[/bold green]")
    console.print("  • OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo")
    console.print("  • Anthropic: claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022")
    console.print("  • Google: gemini-1.5-pro, gemini-1.5-flash")
    console.print("  • And many more via OpenRouter...")


def show_tools_list():
    """Show available tools."""
    console.print("[bold blue]Available Tools:[/bold blue]")
    console.print()
    
    try:
        from ai.tools import list_tools, get_categories
        
        categories = get_categories()
        for category in sorted(categories):
            tools = list_tools(category=category)
            if tools:
                console.print(f"[bold green]{category.title()}:[/bold green]")
                for tool_name in sorted(tools.keys()):
                    tool = tools[tool_name]
                    desc = getattr(tool, 'description', 'No description')
                    console.print(f"  • {tool_name}: {desc}")
                console.print()
    except Exception as e:
        console.print(f"Error listing tools: {e}")


def resolve_tools(tool_specs: List[str]) -> List:
    """Resolve tool specifications to actual tool functions."""
    tools = []
    
    try:
        from ai.tools import get_tool, list_tools
        
        for spec in tool_specs:
            if ':' in spec:
                # Category:tool format
                category, tool_name = spec.split(':', 1)
                tool_dict = list_tools(category=category)
                if tool_name in tool_dict:
                    tools.append(tool_dict[tool_name])
                else:
                    console.print(f"[yellow]Warning: Tool {tool_name} not found in category {category}[/yellow]")
            else:
                # Just tool name
                tool = get_tool(spec)
                if tool:
                    tools.append(tool)
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
    
    # Prefer quality for code generation
    if 'quality' not in kwargs:
        kwargs['quality'] = True


if __name__ == "__main__":
    main()