#!/usr/bin/env python3
"""Clean command-line interface for the AI library with minimal logging."""

import sys
import os
from typing import Optional
from contextlib import redirect_stderr
from io import StringIO
from rich.console import Console
from rich.panel import Panel

console = Console()

def filter_stderr(output):
    """Filter out unwanted error messages while keeping real errors."""
    lines = output.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Skip these specific noise messages
        if any(noise in line for noise in [
            "Task was destroyed but it is pending",
            "sys.meta_path is None",
            "coroutine 'Logging.async_success_handler' was never awaited",
            "Exception ignored in: <function ClientSession.__del__",
            "Exception ignored in: <function BaseConnector.__del__",
            "ImportError: sys.meta_path is None"
        ]):
            continue
        
        # Keep non-empty lines that might be real errors
        if line.strip():
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

def show_help():
    """Show help message."""
    help_text = """
[bold blue]AI Library - Clean Interface[/bold blue]

[bold green]Usage:[/bold green]
  ai "Your question here"                      # Basic usage (uses cloud by default)
  ai "Question" --model MODEL                  # Specify model
  ai "Question" --backend local                # Use local backend (Ollama)
  ai "Question" --stream                       # Stream response
  ai "Question" --verbose                      # Show details
  
[bold green]Commands:[/bold green]
  ai backend-status                            # Check backend status
  ai models-list                               # List available models
  ai --help                                    # Show this help

[bold green]Examples:[/bold green]
  ai "What is Python?"
  ai "Explain quantum computing" --stream
  ai "Tell me a joke" --model openrouter/anthropic/claude-3-haiku
  ai "Debug this code" --verbose
  ai "Local question" --backend local --model llama2
  
[bold green]Environment:[/bold green]
  Default: Uses cloud backend with OpenRouter models
  Set OPENROUTER_API_KEY=your-key for cloud models
  Set OPENAI_API_KEY=your-key for OpenAI models
  Set ANTHROPIC_API_KEY=your-key for Anthropic models
    """
    console.print(help_text)

def clean_execute(func, *args, **kwargs):
    """Execute function with clean error output."""
    # Capture stderr
    stderr_capture = StringIO()
    
    try:
        with redirect_stderr(stderr_capture):
            return func(*args, **kwargs)
    finally:
        # Filter and show only relevant errors
        captured_stderr = stderr_capture.getvalue()
        if captured_stderr:
            filtered_errors = filter_stderr(captured_stderr)
            if filtered_errors.strip():
                # Only show if there are real errors
                console.print(f"[red]Warning:[/red] {filtered_errors}", file=sys.stderr)

def main():
    """Main CLI entry point."""
    # Reduce LiteLLM verbosity
    os.environ["LITELLM_LOG"] = "ERROR"
    
    # Parse simple arguments
    args = sys.argv[1:]
    
    if not args or '--help' in args or '-h' in args:
        show_help()
        return
    
    if args[0] == 'backend-status':
        from .cli_v2 import show_backend_status
        clean_execute(show_backend_status)
        return
    
    if args[0] == 'models-list':
        from .cli_v2 import show_models_list
        clean_execute(show_models_list)
        return
    
    # Parse AI query arguments
    prompt = None
    model = None
    backend = 'cloud'
    stream = False
    verbose = False
    system = None
    temperature = None
    max_tokens = None
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg.startswith('-'):
            if arg in ['--model', '-m'] and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            elif arg in ['--backend', '-b'] and i + 1 < len(args):
                backend = args[i + 1]
                i += 2
            elif arg in ['--system', '-s'] and i + 1 < len(args):
                system = args[i + 1]
                i += 2
            elif arg in ['--temperature', '-t'] and i + 1 < len(args):
                temperature = float(args[i + 1])
                i += 2
            elif arg == '--max-tokens' and i + 1 < len(args):
                max_tokens = int(args[i + 1])
                i += 2
            elif arg == '--stream':
                stream = True
                i += 1
            elif arg in ['--verbose', '-v']:
                verbose = True
                i += 1
            else:
                i += 1
        else:
            if prompt is None:
                prompt = arg
            i += 1
    
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
    if verbose:
        panel_content = f"[bold]Prompt:[/bold] {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
        if model:
            panel_content += f"\n[bold]Model:[/bold] {model}"
        if system:
            panel_content += f"\n[bold]System:[/bold] {system[:50]}{'...' if len(system) > 50 else ''}"
        panel_content += f"\n[bold]Backend:[/bold] {backend}"
        
        console.print(Panel(panel_content, title="AI Request", border_style="blue"))
        console.print()
    
    # Prepare arguments
    kwargs = {}
    if model:
        kwargs['model'] = model
    elif backend == 'cloud':
        # Default to OpenRouter model if using cloud and no model specified
        kwargs['model'] = 'openrouter/google/gemini-flash-1.5'
    
    if system:
        kwargs['system'] = system
    if backend:
        kwargs['backend'] = backend
    if temperature is not None:
        kwargs['temperature'] = temperature
    if max_tokens:
        kwargs['max_tokens'] = max_tokens
    
    try:
        # Import here to avoid import errors
        from .api import ask, stream as stream_func
        
        def execute_ai():
            if stream:
                # Stream response
                console.print("[dim]Streaming response...[/dim]")
                console.print()
                
                for chunk in stream_func(prompt, **kwargs):
                    console.print(chunk, end="")
                console.print()  # Final newline
            else:
                # Regular response
                if verbose:
                    console.print("[dim]Generating response...[/dim]")
                
                response = ask(prompt, **kwargs)
                
                # Print response
                console.print(str(response))
                
                # Show metadata if verbose
                if verbose:
                    console.print()
                    metadata = []
                    metadata.append(f"[bold]Model:[/bold] {response.model}")
                    metadata.append(f"[bold]Backend:[/bold] {response.backend}")
                    metadata.append(f"[bold]Time:[/bold] {response.time:.2f}s")
                    if hasattr(response, 'tokens_in') and response.tokens_in:
                        metadata.append(f"[bold]Tokens In:[/bold] {response.tokens_in}")
                    if hasattr(response, 'tokens_out') and response.tokens_out:
                        metadata.append(f"[bold]Tokens Out:[/bold] {response.tokens_out}")
                    if hasattr(response, 'cost') and response.cost:
                        metadata.append(f"[bold]Cost:[/bold] ${response.cost:.4f}")
                    
                    console.print(Panel("\n".join(metadata), title="Response Metadata", border_style="green"))
        
        clean_execute(execute_ai)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()