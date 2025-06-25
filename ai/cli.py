#!/usr/bin/env python3
"""Simple command-line interface for the AI library."""

import sys
import os
from typing import Optional
from rich.console import Console
from rich.panel import Panel

console = Console()

def show_help():
    """Show help message."""
    help_text = """
[bold blue]AI Library - Unified AI Interface[/bold blue]

[bold green]Usage:[/bold green]
  ai "Your question here"                      # Basic usage
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
  ai "Tell me a joke" --model openrouter/google/gemini-flash-1.5
  ai "Debug this code" --verbose
  ai "Local question" --backend local --model llama2
  
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
        from .backends import LocalBackend
        local = LocalBackend()
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
        from .backends import CloudBackend
        cloud = CloudBackend()
        if cloud.is_available:
            console.print("✅ [green]Cloud Backend:[/green] Available")
            console.print(f"   Default Model: {cloud.default_model}")
            
            # Check API keys
            keys_found = []
            for key_name in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'OPENROUTER_API_KEY']:
                if os.getenv(key_name):
                    keys_found.append(key_name.replace('_API_KEY', ''))
            
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
        from .backends import LocalBackend
        local = LocalBackend()
        if local.is_available:
            # Try to get models from Ollama
            import httpx
            try:
                response = httpx.get(f"{local.base_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    models = response.json().get('models', [])
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


def parse_args():
    """Parse command line arguments manually."""
    args = sys.argv[1:]
    
    if not args or '--help' in args or '-h' in args:
        return {'command': 'help'}
    
    if args[0] == 'backend-status':
        return {'command': 'backend-status'}
    
    if args[0] == 'models-list':
        return {'command': 'models-list'}
    
    # Parse AI query
    result = {
        'command': 'query',
        'prompt': None,
        'model': None,
        'system': None,
        'backend': 'cloud',
        'temperature': None,
        'max_tokens': None,
        'stream': False,
        'verbose': False
    }
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg.startswith('-'):
            if arg in ['--model', '-m'] and i + 1 < len(args):
                result['model'] = args[i + 1]
                i += 2
            elif arg in ['--system', '-s'] and i + 1 < len(args):
                result['system'] = args[i + 1]
                i += 2
            elif arg in ['--backend', '-b'] and i + 1 < len(args):
                result['backend'] = args[i + 1]
                i += 2
            elif arg in ['--temperature', '-t'] and i + 1 < len(args):
                result['temperature'] = float(args[i + 1])
                i += 2
            elif arg == '--max-tokens' and i + 1 < len(args):
                result['max_tokens'] = int(args[i + 1])
                i += 2
            elif arg == '--stream':
                result['stream'] = True
                i += 1
            elif arg in ['--verbose', '-v']:
                result['verbose'] = True
                i += 1
            else:
                i += 1
        else:
            # This should be the prompt
            if result['prompt'] is None:
                result['prompt'] = arg
            i += 1
    
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
    
    # Context manager to suppress cleanup warnings
    @contextlib.contextmanager
    def suppress_cleanup_warnings():
        import warnings
        import logging
        
        # Temporarily suppress specific warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*Task was destroyed.*")
            warnings.filterwarnings("ignore", message=".*sys.meta_path.*")
            warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*")
            
            # Suppress aiohttp deletion warnings
            logging.getLogger("aiohttp").setLevel(logging.CRITICAL)
            
            yield
    
    try:
        args = parse_args()
        
        if args['command'] == 'help':
            show_help()
            return
        
        if args['command'] == 'backend-status':
            show_backend_status()
            return
        
        if args['command'] == 'models-list':
            show_models_list()
            return
        
        if args['command'] == 'query':
            prompt = args['prompt']
            
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
            if args['verbose']:
                panel_content = f"[bold]Prompt:[/bold] {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
                if args['model']:
                    panel_content += f"\n[bold]Model:[/bold] {args['model']}"
                if args['system']:
                    panel_content += f"\n[bold]System:[/bold] {args['system'][:50]}{'...' if len(args['system']) > 50 else ''}"
                panel_content += f"\n[bold]Backend:[/bold] {args['backend']}"
                
                console.print(Panel(panel_content, title="AI Request", border_style="blue"))
                console.print()
            
            # Prepare arguments
            kwargs = {}
            if args['model']:
                kwargs['model'] = args['model']
            elif args['backend'] == 'cloud':
                # Default to OpenRouter model if using cloud and no model specified
                kwargs['model'] = 'openrouter/google/gemini-flash-1.5'
            if args['system']:
                kwargs['system'] = args['system']
            if args['backend']:
                kwargs['backend'] = args['backend']
            if args['temperature'] is not None:
                kwargs['temperature'] = args['temperature']
            if args['max_tokens']:
                kwargs['max_tokens'] = args['max_tokens']
            
            # Import here to avoid import errors
            from .api import ask, stream
            
            # Use context manager to suppress cleanup warnings
            with suppress_cleanup_warnings():
                if args['stream']:
                    # Stream response
                    console.print("[dim]Streaming response...[/dim]")
                    console.print()
                    
                    for chunk in stream(prompt, **kwargs):
                        console.print(chunk, end="")
                    console.print()  # Final newline
                else:
                    # Regular response
                    if args['verbose']:
                        console.print("[dim]Generating response...[/dim]")
                    
                    response = ask(prompt, **kwargs)
                    
                    # Print response
                    console.print(str(response))
                    
                    # Show metadata if verbose
                    if args['verbose']:
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
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        # Import exceptions for better error handling
        from .exceptions import (
            APIKeyError, ModelNotFoundError, RateLimitError, 
            BackendNotAvailableError, EmptyResponseError
        )
        
        # Provide user-friendly error messages based on exception type
        if isinstance(e, APIKeyError):
            console.print(f"[red]❌ API Key Missing:[/red] {e}")
            console.print(f"[yellow]Set your API key in the .env file: {e.details.get('env_var', 'API_KEY')}[/yellow]")
            sys.exit(1)
        elif isinstance(e, ModelNotFoundError):
            console.print(f"[red]❌ Model Not Found:[/red] {e}")
            console.print("[yellow]Run 'ai models-list' to see available models[/yellow]")
            sys.exit(1)
        elif isinstance(e, RateLimitError):
            console.print(f"[red]⏱️ Rate Limit Exceeded:[/red] {e}")
            retry_after = e.details.get('retry_after')
            if retry_after:
                console.print(f"[yellow]Wait {retry_after} seconds before retrying[/yellow]")
            else:
                console.print("[yellow]Wait a moment before retrying[/yellow]")
            sys.exit(1)
        elif isinstance(e, BackendNotAvailableError):
            console.print(f"[red]🔌 Backend Not Available:[/red] {e}")
            console.print("[yellow]Run 'ai backend-status' to check connectivity[/yellow]")
            sys.exit(1)
        elif isinstance(e, EmptyResponseError):
            console.print(f"[red]❌ Empty Response:[/red] {e}")
            console.print("[yellow]The AI returned an empty response. Try rephrasing your question.[/yellow]")
            sys.exit(1)
        else:
            # Generic error handling
            console.print(f"[red]❌ Error:[/red] {e}")
            if args.get('verbose'):
                import traceback
                console.print("\n[dim]Full traceback:[/dim]")
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
            else:
                console.print("[yellow]Use --verbose flag for more details[/yellow]")
            sys.exit(1)


if __name__ == "__main__":
    main()