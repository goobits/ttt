#!/usr/bin/env python3
"""Simple command-line interface for the AI library."""

import sys
import os
from typing import Optional, List
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
  ai "Question" --tools "module:function,..."  # Use tools/functions
  
[bold green]Commands:[/bold green]
  ai backend-status                            # Check backend status
  ai models-list                               # List available models
  ai tools-list                                # List available tools
  ai --help                                    # Show this help

[bold green]Examples:[/bold green]
  ai "What is Python?"
  ai "Explain quantum computing" --stream
  ai "Tell me a joke" --model openrouter/google/gemini-flash-1.5
  ai "Debug this code" --verbose
  ai "Local question" --backend local --model llama2
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


def show_tools_list():
    """Show available tools."""
    console.print("[bold blue]Available Tools:[/bold blue]")
    console.print()
    
    try:
        from .tools.registry import get_registry
        from .tools import list_tools
        
        # Get all tools grouped by category
        registry = get_registry()
        all_tools = list_tools()
        
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
        if ':' in spec:
            # Module:function or path:function format
            module_path, function_name = spec.rsplit(':', 1)
            
            try:
                if module_path.endswith('.py') or '/' in module_path or '\\' in module_path:
                    # File path - load module from file
                    import importlib.util
                    spec_loader = importlib.util.spec_from_file_location("tool_module", module_path)
                    if spec_loader and spec_loader.loader:
                        module = importlib.util.module_from_spec(spec_loader)
                        spec_loader.loader.exec_module(module)
                        if hasattr(module, function_name):
                            resolved_tools.append(getattr(module, function_name))
                        else:
                            console.print(f"[yellow]Warning: Function '{function_name}' not found in {module_path}[/yellow]")
                else:
                    # Module name - import normally
                    import importlib
                    module = importlib.import_module(module_path)
                    if hasattr(module, function_name):
                        resolved_tools.append(getattr(module, function_name))
                    else:
                        console.print(f"[yellow]Warning: Function '{function_name}' not found in module {module_path}[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load tool '{spec}': {e}[/yellow]")
        else:
            # Just function name - try to get from registry
            from .tools.registry import get_tool
            tool = get_tool(spec)
            if tool:
                resolved_tools.append(tool)
            else:
                console.print(f"[yellow]Warning: Tool '{spec}' not found in registry[/yellow]")
    
    return resolved_tools


def parse_args():
    """Parse command line arguments manually."""
    args = sys.argv[1:]
    
    if not args or '--help' in args or '-h' in args:
        return {'command': 'help'}
    
    if args[0] == 'backend-status':
        return {'command': 'backend-status'}
    
    if args[0] == 'models-list':
        return {'command': 'models-list'}
    
    if args[0] == 'tools-list' or args[0] == 'tools':
        return {'command': 'tools-list'}
    
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
        'verbose': False,
        'tools': []
    }
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg.startswith('-') and arg != '-':
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
            elif arg == '--tools' and i + 1 < len(args):
                # Parse comma-separated tool specifications
                tools_str = args[i + 1]
                result['tools'] = [t.strip() for t in tools_str.split(',') if t.strip()]
                i += 2
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
        
        if args['command'] == 'tools-list':
            show_tools_list()
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
            
            # Resolve tools if specified
            if args['tools']:
                resolved_tools = resolve_tools(args['tools'])
                if resolved_tools:
                    kwargs['tools'] = resolved_tools
                    if args['verbose']:
                        console.print(f"[dim]Loaded {len(resolved_tools)} tools[/dim]")
                        # Show tool execution stats if available
                        try:
                            from .tools.executor import get_execution_stats
                            stats = get_execution_stats()
                            if stats['total_calls'] > 0:
                                console.print(f"[dim]Tool execution stats: {stats['success_rate']:.1%} success rate, avg {stats['avg_execution_time']:.2f}s[/dim]")
                        except:
                            pass
            
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
                        
                        # Add tool call information if available
                        if hasattr(response, 'tool_calls') and response.tool_calls:
                            metadata.append(f"[bold]Tools Called:[/bold] {len(response.tool_calls)}")
                            for call in response.tool_calls:
                                status = "✓" if call.succeeded else "✗"
                                metadata.append(f"  {status} {call.name}({', '.join(f'{k}={v}' for k, v in call.arguments.items())})")
                        
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