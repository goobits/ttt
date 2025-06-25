"""Command-line interface for the AI library."""

import sys
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live

from .api import ask, stream
from .utils import get_logger, console
from .backends import LocalBackend, CloudBackend
from .config import model_registry, get_config


app = typer.Typer(
    name="ai",
    help="The Unified AI Library - Ask questions, get answers",
    add_completion=False,
)
logger = get_logger(__name__)


@app.command()
def main(
    prompt: str = typer.Argument(
        ..., 
        help="Your question or prompt"
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model", "-m",
        help="Specific model to use"
    ),
    system: Optional[str] = typer.Option(
        None,
        "--system", "-s", 
        help="System prompt to set context"
    ),
    backend: Optional[str] = typer.Option(
        "local",
        "--backend", "-b",
        help="Backend to use (local, cloud)"
    ),
    temperature: Optional[float] = typer.Option(
        None,
        "--temperature", "-t",
        help="Sampling temperature (0.0 to 1.0)"
    ),
    max_tokens: Optional[int] = typer.Option(
        None,
        "--max-tokens",
        help="Maximum tokens to generate"
    ),
    stream_output: bool = typer.Option(
        False,
        "--stream",
        help="Stream the response token by token"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show detailed information"
    ),
):
    """
    Ask the AI a question and get an answer.
    
    Examples:
        ai "What is Python?"
        ai "Explain quantum computing" --stream
        ai "Debug this code" --system "You are a code reviewer"
        ai "Tell me a joke" --model llama2 --verbose
    """
    # Read from stdin if prompt is "-"
    if prompt == "-":
        prompt = sys.stdin.read().strip()
        if not prompt:
            console.print("[red]No input provided[/red]")
            raise typer.Exit(1)
    
    # Show what we're doing if verbose
    if verbose:
        panel_content = f"[bold]Prompt:[/bold] {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
        if model:
            panel_content += f"\n[bold]Model:[/bold] {model}"
        if system:
            panel_content += f"\n[bold]System:[/bold] {system[:50]}{'...' if len(system) > 50 else ''}"
        panel_content += f"\n[bold]Backend:[/bold] {backend}"
        
        console.print(Panel(panel_content, title="AI Request", border_style="blue"))
    
    try:
        if stream_output:
            # Streaming mode
            if verbose:
                console.print("\n[bold green]Response (streaming):[/bold green]")
            else:
                # Just start streaming immediately
                pass
            
            for chunk in stream(
                prompt,
                model=model,
                system=system,
                backend=backend,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                console.print(chunk, end="")
            
            console.print()  # Final newline
            
        else:
            # Non-streaming mode with spinner
            with console.status("[bold green]Thinking...") as status:
                response = ask(
                    prompt,
                    model=model,
                    system=system,
                    backend=backend,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            
            if response.failed:
                console.print(f"[bold red]Error:[/bold red] {response.error}")
                raise typer.Exit(1)
            
            # Show the response
            if verbose:
                console.print(f"\n[bold green]Response:[/bold green]")
                console.print(str(response))
                
                # Show metadata
                metadata_content = f"[bold]Model:[/bold] {response.model}"
                metadata_content += f"\n[bold]Backend:[/bold] {response.backend}"
                if response.time_taken:
                    metadata_content += f"\n[bold]Time:[/bold] {response.time_taken:.2f}s"
                if response.tokens_in:
                    metadata_content += f"\n[bold]Tokens in:[/bold] {response.tokens_in}"
                if response.tokens_out:
                    metadata_content += f"\n[bold]Tokens out:[/bold] {response.tokens_out}"
                
                console.print(Panel(metadata_content, title="Response Metadata", border_style="green"))
            else:
                # Just show the response text
                console.print(str(response))
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            logger.exception("Command failed")
        raise typer.Exit(1)


# Create models subcommand group
models_app = typer.Typer(name="models", help="Manage AI models")
app.add_typer(models_app, name="models")


@models_app.command("list")
def models_list(
    local: bool = typer.Option(False, "--local", "-l", help="Show only local models"),
    cloud: bool = typer.Option(False, "--cloud", "-c", help="Show only cloud models"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed model information"),
):
    """List all available models across backends."""
    from rich.table import Table
    from rich.text import Text
    import asyncio
    
    # Determine which backends to show
    show_local = local or (not local and not cloud)
    show_cloud = cloud or (not local and not cloud)
    
    console.print("[bold]AI Models[/bold]\n")
    
    # Collect all models
    all_models = []
    
    # Get models from registry (includes cloud models)
    if show_cloud:
        for model_info in model_registry.list_models():
            all_models.append({
                "name": model_info.name,
                "backend": "cloud",
                "provider": model_info.provider,
                "aliases": model_info.aliases,
                "speed": model_info.speed,
                "quality": model_info.quality,
                "capabilities": model_info.capabilities,
                "context_length": model_info.context_length,
            })
    
    # Get local models if available
    if show_local:
        try:
            backend = LocalBackend()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                local_models = loop.run_until_complete(backend.models())
                for model in local_models:
                    # Check if it's already in registry
                    if not any(m["name"] == model for m in all_models):
                        all_models.append({
                            "name": model,
                            "backend": "local",
                            "provider": "ollama",
                            "aliases": [],
                            "speed": "varies",
                            "quality": "varies",
                            "capabilities": ["text"],
                            "context_length": None,
                        })
            finally:
                loop.close()
        except Exception as e:
            if show_local and not show_cloud:
                console.print(f"[yellow]Warning: Could not connect to local backend: {e}[/yellow]")
    
    if not all_models:
        console.print("[yellow]No models found.[/yellow]")
        if show_local:
            console.print("\nFor local models, make sure Ollama is running:")
            console.print("  [bold]ollama serve[/bold]")
            console.print("\nThen pull a model:")
            console.print("  [bold]ollama pull llama2[/bold]")
        return
    
    # Create table
    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Backend", style="green")
    table.add_column("Provider", style="blue")
    
    if verbose:
        table.add_column("Aliases", style="yellow")
        table.add_column("Speed", style="magenta")
        table.add_column("Quality", style="magenta")
        table.add_column("Capabilities", style="white")
        table.add_column("Context", style="dim")
    else:
        table.add_column("Aliases", style="yellow")
    
    # Sort models by backend and name
    all_models.sort(key=lambda x: (x["backend"], x["name"]))
    
    # Add rows
    for model in all_models:
        if verbose:
            table.add_row(
                model["name"],
                model["backend"],
                model["provider"],
                ", ".join(model["aliases"]) if model["aliases"] else "-",
                model["speed"] or "-",
                model["quality"] or "-",
                ", ".join(model["capabilities"]) if model["capabilities"] else "-",
                f"{model['context_length']:,}" if model["context_length"] else "-"
            )
        else:
            table.add_row(
                model["name"],
                model["backend"],
                model["provider"],
                ", ".join(model["aliases"][:2]) + ("..." if len(model["aliases"]) > 2 else "") if model["aliases"] else "-",
            )
    
    console.print(table)
    
    # Show summary
    local_count = sum(1 for m in all_models if m["backend"] == "local")
    cloud_count = sum(1 for m in all_models if m["backend"] == "cloud")
    
    console.print(f"\n[dim]Total: {len(all_models)} models ({local_count} local, {cloud_count} cloud)[/dim]")
    
    # Show tips
    if not verbose:
        console.print("\n[dim]Tip: Use --verbose to see more details[/dim]")


@models_app.command("pull")
def models_pull(
    model_name: str = typer.Argument(..., help="Name of the model to pull"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed progress"),
):
    """Pull a model for the local Ollama backend."""
    import subprocess
    import shutil
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    
    # Check if ollama is installed
    if not shutil.which("ollama"):
        console.print("[red]Error: Ollama is not installed or not in PATH[/red]")
        console.print("\nInstall Ollama from: https://ollama.ai")
        raise typer.Exit(1)
    
    # Check if Ollama is running
    try:
        backend = LocalBackend()
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            status = loop.run_until_complete(backend.status())
            if not status.get("available"):
                console.print("[yellow]Warning: Ollama doesn't appear to be running[/yellow]")
                console.print("Start it with: [bold]ollama serve[/bold]")
        finally:
            loop.close()
    except Exception:
        pass
    
    console.print(f"[bold]Pulling model:[/bold] {model_name}")
    
    try:
        if verbose:
            # Run with full output
            result = subprocess.run(
                ["ollama", "pull", model_name],
                text=True,
                check=True
            )
        else:
            # Run with progress indication
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(f"Downloading {model_name}...", total=None)
                
                process = subprocess.Popen(
                    ["ollama", "pull", model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Parse output for progress
                for line in process.stdout:
                    line = line.strip()
                    if "pulling" in line.lower():
                        progress.update(task, description=f"Pulling {model_name}...")
                    elif "verifying" in line.lower():
                        progress.update(task, description=f"Verifying {model_name}...")
                    elif "success" in line.lower() or "already up to date" in line.lower():
                        progress.update(task, description=f"Complete: {model_name}")
                    
                    if verbose:
                        console.print(f"[dim]{line}[/dim]")
                
                process.wait()
                
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, ["ollama", "pull", model_name])
        
        console.print(f"\n[green]✓ Successfully pulled {model_name}[/green]")
        
        # Test the model
        console.print("\n[dim]Testing model...[/dim]")
        test_response = ask(f"Say 'Hello' in one word", model=model_name, backend="local")
        if not test_response.failed:
            console.print(f"[green]✓ Model is working![/green]")
        else:
            console.print(f"[yellow]⚠ Model pulled but test failed: {test_response.error}[/yellow]")
            
    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]Error pulling model: {e}[/red]")
        if "not found" in str(e).lower():
            console.print("\n[yellow]Model not found. Check available models at:[/yellow]")
            console.print("https://ollama.ai/library")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


# Create backend subcommand group
backend_app = typer.Typer(name="backend", help="Manage AI backends")
app.add_typer(backend_app, name="backend")


@backend_app.command("status")
def backend_status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed status information"),
):
    """Check connectivity and status of all configured backends."""
    from rich.table import Table
    import asyncio
    import os
    
    console.print("[bold]AI Backend Status[/bold]\n")
    
    # Create status table
    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Backend", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")
    if verbose:
        table.add_column("Configuration", style="yellow")
    
    # Check local backend (Ollama)
    local_status = "🔴 Offline"
    local_details = "Not available"
    local_config = ""
    
    try:
        backend = LocalBackend()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            status_info = loop.run_until_complete(backend.status())
            if status_info.get("available"):
                local_status = "🟢 Online"
                model_count = len(status_info.get("models", []))
                local_details = f"{model_count} models available"
                if verbose:
                    base_url = status_info.get("base_url", config.ollama_base_url)
                    local_config = f"URL: {base_url}"
            else:
                local_details = "Ollama not running"
                if verbose:
                    local_config = f"URL: {config.ollama_base_url}"
        finally:
            loop.close()
    except Exception as e:
        local_details = f"Error: {str(e)}"
        if verbose:
            local_config = f"URL: {config.ollama_base_url}"
    
    if verbose:
        table.add_row("Local (Ollama)", local_status, local_details, local_config)
    else:
        table.add_row("Local (Ollama)", local_status, local_details)
    
    # Check cloud backends
    cloud_providers = {
        "openai": {
            "name": "OpenAI",
            "env_key": "OPENAI_API_KEY",
            "test_model": "gpt-3.5-turbo",
        },
        "anthropic": {
            "name": "Anthropic",
            "env_key": "ANTHROPIC_API_KEY",
            "test_model": "claude-3-haiku-20240307",
        },
        "google": {
            "name": "Google",
            "env_key": "GOOGLE_API_KEY",
            "test_model": "gemini-pro",
        },
    }
    
    for provider_id, provider_info in cloud_providers.items():
        status = "🔴 No Key"
        details = "API key not configured"
        config_info = ""
        
        # Check if API key is set
        api_key = os.environ.get(provider_info["env_key"])
        if api_key:
            # Key is present, test connectivity
            status = "🟡 Testing..."
            details = "Checking connectivity..."
            
            try:
                # Quick test with minimal tokens
                test_response = ask(
                    "Hi",
                    model=provider_info["test_model"],
                    backend="cloud",
                    max_tokens=5,
                )
                
                if not test_response.failed:
                    status = "🟢 Ready"
                    details = "API key valid, connection successful"
                    if verbose:
                        config_info = f"Key: {api_key[:8]}...{api_key[-4:]}"
                else:
                    status = "🟠 Error"
                    error_msg = str(test_response.error)
                    if "401" in error_msg or "invalid" in error_msg.lower():
                        details = "Invalid API key"
                    elif "429" in error_msg:
                        details = "Rate limited"
                    elif "timeout" in error_msg.lower():
                        details = "Connection timeout"
                    else:
                        details = f"Error: {error_msg[:50]}..."
                    if verbose:
                        config_info = f"Key: {api_key[:8]}...{api_key[-4:]}"
                        
            except Exception as e:
                status = "🟠 Error"
                details = f"Test failed: {str(e)[:50]}..."
                if verbose:
                    config_info = f"Key: {api_key[:8]}...{api_key[-4:]}"
        else:
            if verbose:
                config_info = f"Env: {provider_info['env_key']}"
        
        if verbose:
            table.add_row(f"Cloud ({provider_info['name']})", status, details, config_info)
        else:
            table.add_row(f"Cloud ({provider_info['name']})", status, details)
    
    console.print(table)
    
    # Show summary and tips
    console.print("\n[bold]Legend:[/bold]")
    console.print("  🟢 Ready     - Backend is fully operational")
    console.print("  🟡 Testing   - Checking connectivity...")
    console.print("  🟠 Error     - Backend has issues")
    console.print("  🔴 Offline   - Backend not available")
    
    # Show configuration tips
    console.print("\n[bold]Configuration Tips:[/bold]")
    
    # Check for missing keys
    missing_keys = []
    for provider_id, provider_info in cloud_providers.items():
        if not os.environ.get(provider_info["env_key"]):
            missing_keys.append(provider_info)
    
    if missing_keys:
        console.print("\n[yellow]Missing API keys:[/yellow]")
        for provider in missing_keys:
            console.print(f"  export {provider['env_key']}=your-api-key")
    
    # Local backend tips
    try:
        import shutil
        if not shutil.which("ollama"):
            console.print("\n[yellow]Ollama not installed:[/yellow]")
            console.print("  Install from: https://ollama.ai")
    except:
        pass
    
    if verbose:
        console.print("\n[dim]Configuration file: ~/.config/ai/config.yaml[/dim]")


@app.command()
def version():
    """Show version information."""
    from . import __version__
    console.print(f"AI Library version {__version__}")


if __name__ == "__main__":
    app()