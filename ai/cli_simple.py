#!/usr/bin/env python3
"""Simple command-line interface for the AI library."""

import sys
import argparse
from typing import Optional
from rich.console import Console
from rich.panel import Panel

from .api import ask, stream
from .backends import LocalBackend, CloudBackend
from .config import get_config

console = Console()


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog='ai',
        description='The Unified AI Library - Ask questions, get answers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai "What is Python?"
  ai "Explain quantum computing" --stream
  ai "Debug this code" --system "You are a code reviewer"
  ai "Tell me a joke" --model llama2 --verbose
  ai backend status
  ai models list
        """
    )
    
    # Main command options
    parser.add_argument(
        'prompt',
        nargs='?',
        help='Your question or prompt (use "-" to read from stdin)'
    )
    
    parser.add_argument(
        '--model', '-m',
        help='Specific model to use'
    )
    
    parser.add_argument(
        '--system', '-s',
        help='System prompt to set context'
    )
    
    parser.add_argument(
        '--backend', '-b',
        default='local',
        choices=['local', 'cloud'],
        help='Backend to use (default: local)'
    )
    
    parser.add_argument(
        '--temperature', '-t',
        type=float,
        help='Sampling temperature (0.0 to 1.0)'
    )
    
    parser.add_argument(
        '--max-tokens',
        type=int,
        help='Maximum tokens to generate'
    )
    
    parser.add_argument(
        '--stream',
        action='store_true',
        help='Stream the response token by token'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Backend command
    backend_parser = subparsers.add_parser('backend', help='Backend management')
    backend_subparsers = backend_parser.add_subparsers(dest='backend_action', help='Backend actions')
    backend_subparsers.add_parser('status', help='Show backend status')
    
    # Models command  
    models_parser = subparsers.add_parser('models', help='Model management')
    models_subparsers = models_parser.add_subparsers(dest='models_action', help='Model actions')
    models_subparsers.add_parser('list', help='List available models')
    
    return parser


def handle_backend_command(action: str, verbose: bool = False):
    """Handle backend subcommands."""
    if action == 'status':
        console.print("[bold blue]Backend Status:[/bold blue]")
        console.print()
        
        # Check local backend
        try:
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
            cloud = CloudBackend()
            if cloud.is_available:
                console.print("✅ [green]Cloud Backend:[/green] Available")
                console.print(f"   Default Model: {cloud.default_model}")
                
                # Check API keys
                import os
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


def handle_models_command(action: str, verbose: bool = False):
    """Handle models subcommands."""
    if action == 'list':
        console.print("[bold blue]Available Models:[/bold blue]")
        console.print()
        
        # Local models
        console.print("[bold green]Local Models (Ollama):[/bold green]")
        try:
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


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle subcommands
    if args.command == 'backend':
        handle_backend_command(args.backend_action, args.verbose)
        return
    elif args.command == 'models':
        handle_models_command(args.models_action, args.verbose)
        return
    
    # Main AI query
    if not args.prompt:
        parser.print_help()
        return
    
    prompt = args.prompt
    
    # Read from stdin if prompt is "-"
    if prompt == "-":
        prompt = sys.stdin.read().strip()
        if not prompt:
            console.print("[red]No input provided[/red]")
            sys.exit(1)
    
    # Show what we're doing if verbose
    if args.verbose:
        panel_content = f"[bold]Prompt:[/bold] {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
        if args.model:
            panel_content += f"\n[bold]Model:[/bold] {args.model}"
        if args.system:
            panel_content += f"\n[bold]System:[/bold] {args.system[:50]}{'...' if len(args.system) > 50 else ''}"
        panel_content += f"\n[bold]Backend:[/bold] {args.backend}"
        
        console.print(Panel(panel_content, title="AI Request", border_style="blue"))
        console.print()
    
    # Prepare arguments
    kwargs = {}
    if args.model:
        kwargs['model'] = args.model
    if args.system:
        kwargs['system'] = args.system
    if args.backend:
        kwargs['backend'] = args.backend
    if args.temperature is not None:
        kwargs['temperature'] = args.temperature
    if args.max_tokens:
        kwargs['max_tokens'] = args.max_tokens
    
    try:
        if args.stream:
            # Stream response
            console.print("[dim]Streaming response...[/dim]")
            console.print()
            
            for chunk in stream(prompt, **kwargs):
                console.print(chunk, end="")
            console.print()  # Final newline
        else:
            # Regular response
            if args.verbose:
                console.print("[dim]Generating response...[/dim]")
            
            response = ask(prompt, **kwargs)
            
            # Print response
            console.print(str(response))
            
            # Show metadata if verbose
            if args.verbose:
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
        console.print(f"[red]Error:[/red] {e}")
        if args.verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()