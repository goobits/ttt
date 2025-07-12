# AI Library Migration Proposal & Implementation Plan

## Overview

This proposal outlines the complete migration of the `agents` directory to implement the enhanced local-first AI system that absorbs the best features of the LLM directory while maintaining no backward compatibility burden.

## Executive Summary

**Goal**: Transform the current cloud-focused AI library into a streamlined, local-first tool that provides:
- Zero-config Ollama integration with smart model selection
- LLM-style coding mode and optimized prompts
- Simplified but powerful CLI with proper subcommand structure
- Enhanced security and reduced complexity
- Clean migration path without legacy code

**Strategy**: Aggressive refactoring with no backward compatibility concerns, focusing on the refined hybrid API specification.

---

## Current State Analysis

### Strengths to Preserve ✅
- **CLI Design**: Clean interface with Rich terminal UI
- **Configuration System**: Multi-source YAML config architecture  
- **Backend Abstraction**: BaseBackend pattern for extensibility
- **Tool Decorator**: `@tool` pattern for easy function creation
- **Error Handling**: Comprehensive exception hierarchy
- **Project Structure**: Well-organized modular design

### Components to Remove ❌
- **Cloud Backend**: LiteLLM dependencies and cloud provider integrations
- **Complex Routing**: Multi-provider smart routing complexity
- **Network Tools**: Web search, HTTP requests (security risk)
- **Code Execution**: `run_python` tool (security risk)
- **Plugin System**: Complex dynamic loading (unnecessary complexity)

### Dependencies to Remove
```toml
# Remove these dependencies
litellm = "^1.0.0"      # Cloud provider integration
bleach = "^6.0.0"       # Web sanitization (no longer needed)
validators = "^0.22.0"  # Web validation (no longer needed)
typer = "^0.12.0"       # CLI framework (replace with argparse subparsers)
```

### Dependencies to Keep
```toml
# Keep these dependencies  
python = "^3.8"
pydantic = "^2.0.0"     # Data validation
rich = "^13.0.0"        # Terminal UI
python-dotenv = "^1.0.0" # Environment management
pyyaml = "^6.0"         # Configuration
httpx = "^0.25.0"       # Local HTTP for Ollama
```

---

## Implementation Plan & Checklist

### Pre-Migration Setup

#### Backup Current State
- [ ] Create branch: `git checkout -b agents-migration`
- [ ] Backup current config: `cp -r ai/ ai-backup/`
- [ ] Document current dependencies: `pip freeze > current-deps.txt`

---

## Phase 1: Infrastructure Changes (Week 1-2)

> **Note**: This phase is intentionally longer as it involves core architectural changes that need to be done carefully.

### Day 1-2: Dependency Cleanup

#### Remove Cloud Dependencies
- [ ] Edit `pyproject.toml`:
  ```toml
  # Remove these lines:
  litellm = "^1.0.0"
  bleach = "^6.0.0" 
  validators = "^0.22.0"
  typer = "^0.12.0"
  
  # Keep these:
  python = "^3.8"
  pydantic = "^2.0.0"
  rich = "^13.0.0"
  python-dotenv = "^1.0.0"
  pyyaml = "^6.0"
  httpx = "^0.25.0"
  ```

#### Update Package Exports
- [ ] Edit `ai/__init__.py`:
  ```python
  # Remove cloud-related imports:
  # from .backends import CloudBackend
  # from .routing import router
  
  # Update __all__ list to remove cloud exports
  ```

### Day 3-4: Remove Cloud Backend

#### Delete Cloud Files
- [ ] `rm ai/backends/cloud.py`
- [ ] `rm ai/routing.py`
- [ ] Update `ai/backends/__init__.py`:
  ```python
  from .base import BaseBackend
  from .local import LocalBackend
  # Remove: from .cloud import CloudBackend
  
  __all__ = ["BaseBackend", "LocalBackend"]  # Remove CloudBackend
  ```

#### Simplify API Layer
- [ ] Edit `ai/api.py`:
  ```python
  # Remove imports:
  # from .backends import CloudBackend
  # from .routing import router
  
  # Replace _get_default_backend():
  def _get_default_backend() -> BaseBackend:
      """Always return LocalBackend."""
      backend = LocalBackend()
      if not backend.is_available:
          raise BackendNotAvailableError("Ollama not available. Run 'ai --setup'")
      return backend
  
  # Simplify ask() function - remove routing logic
  # Simplify stream() function - remove routing logic
  ```

### Day 5-6: Tool System Security

#### Create Security Module
- [ ] Create `ai/security.py`:
  ```python
  from pathlib import Path
  from typing import List
  from .exceptions import SecurityError
  from .config import get_config
  
  def get_allowed_paths(operation: str = "read") -> List[Path]:
      """Get allowed paths from configuration."""
      config = get_config()
      security_config = config.get("security", {})
      
      if operation == "read":
          paths = security_config.get("allowed_read_paths", [
              "~/.config/ai",
              "~/Documents", 
              "~/Downloads",
              "."  # Current directory
          ])
      else:  # write
          paths = security_config.get("allowed_write_paths", [
              "~/Documents",
              "~/Downloads", 
              "./output"  # Output subdirectory
          ])
      
      return [Path(p).expanduser().resolve() for p in paths]
  
  def validate_file_path(path: str, operation: str = "read") -> Path:
      """Validate file path for security."""
      path_obj = Path(path).expanduser().resolve()
      
      # Prevent directory traversal
      if ".." in str(path_obj):
          raise SecurityError("Directory traversal not allowed")
      
      # Check against allowed paths
      allowed_paths = get_allowed_paths(operation)
      if not any(path_obj.is_relative_to(allowed_dir) for allowed_dir in allowed_paths):
          raise SecurityError(f"Access denied to {path_obj}. Allowed paths: {allowed_paths}")
          
      return path_obj
  
  def is_safe_file_operation(path: Path, operation: str) -> bool:
      """Check if file operation is safe."""
      # File size limits
      if operation == "write" and path.exists() and path.stat().st_size > 10_000_000:  # 10MB
          return False
      
      # File type restrictions
      dangerous_extensions = {'.exe', '.bat', '.sh', '.ps1', '.scr'}
      if path.suffix.lower() in dangerous_extensions:
          return False
          
      return True
  ```

#### Remove Unsafe Tools and Secure File Operations
- [ ] Edit `ai/tools/builtins.py`:
  ```python
  # Remove these functions entirely:
  # - web_search
  # - http_request  
  # - run_python
  
  from ..security import validate_file_path, is_safe_file_operation
  
  @tool(category="file", description="Read file contents safely")
  def read_file(file_path: str) -> str:
      """Read file contents safely."""
      path = validate_file_path(file_path, "read")
      if not path.exists():
          raise FileNotFoundError(f"File not found: {file_path}")
      if not path.is_file():
          raise ValueError(f"Path is not a file: {file_path}")
      return path.read_text(encoding='utf-8')
  
  @tool(category="file") 
  def write_file(file_path: str, content: str) -> str:
      """Write content to file safely."""
      path = validate_file_path(file_path, "write")
      if not is_safe_file_operation(path, "write"):
          raise SecurityError("File operation not permitted")
      
      # Create parent directories if needed
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(content, encoding='utf-8')
      return f"Content written to {file_path}"
  
  @tool(category="file")
  def list_directory(directory_path: str = ".") -> str:
      """List directory contents safely."""
      path = validate_file_path(directory_path, "read")
      if not path.exists():
          raise FileNotFoundError(f"Directory not found: {directory_path}")
      if not path.is_dir():
          raise ValueError(f"Path is not a directory: {directory_path}")
      
      items = []
      for item in path.iterdir():
          if item.is_dir():
              items.append(f"📁 {item.name}/")
          else:
              size = item.stat().st_size
              items.append(f"📄 {item.name} ({size} bytes)")
      
      return "\n".join(sorted(items))
  ```

### Day 7-8: Enhanced Local Backend

#### Add Qwen Model Support and Management
- [ ] Edit `ai/backends/local.py`:
  ```python
  class LocalBackend(BaseBackend):
      def __init__(self, config: Optional[Dict[str, Any]] = None):
          super().__init__(config)
          self.base_url = self.backend_config.get("base_url", "http://localhost:11434")
          self.qwen_models = {
              "general": "qwen2.5:32b",
              "coding": "qwen2.5-coder:7b"
          }
          self.fallback_models = ["llama3:8b", "llama2:7b"]
      
      async def get_optimal_model(self, task_type: str = "general") -> str:
          """Get best available model for task based on configuration."""
          from ..config import get_config
          config = get_config()
          available = await self.models()
          
          # Check for advanced 'task_models' config first (triggers advanced mode)
          if config.task_models and task_type in config.task_models:
              for model in config.task_models[task_type]:
                  if model in available:
                      return model
          
          # Fallback to simple 'default_models' list
          for model in config.default_models:
              if model in available:
                  return model
                  
          # Use any available model as last resort
          if available:
              return available[0]
              
          # Suggest the first configured model for the task type
          suggested_model = (
              config.task_models.get(task_type, config.default_models)[0] 
              if config.task_models and task_type in config.task_models 
              else config.default_models[0] if config.default_models 
              else "qwen2.5:32b"
          )
          raise ModelNotFoundError(f"No suitable models found. Run 'ai models pull {suggested_model}'")
      
      async def pull_model(self, model_name: str) -> bool:
          """Pull model via Ollama API."""
          try:
              async with httpx.AsyncClient(timeout=600) as client:
                  response = await client.post(
                      f"{self.base_url}/api/pull",
                      json={"name": model_name}
                  )
                  return response.status_code == 200
          except Exception:
              return False
      
      async def remove_model(self, model_name: str) -> bool:
          """Remove model via Ollama API."""
          try:
              async with httpx.AsyncClient(timeout=30) as client:
                  response = await client.delete(
                      f"{self.base_url}/api/delete",
                      json={"name": model_name}
                  )
                  return response.status_code == 200
          except Exception:
              return False
  ```

---

## Phase 2: Configuration & CLI (Week 2-3)

### Day 9-10: Simplify Configuration

#### Update Configuration Model with Security Settings
- [ ] Edit `ai/config.py`:
  ```python
  DEFAULT_CONFIG = {
      "ollama": {
          "base_url": "http://localhost:11434",
          "timeout": 60,
          "setup_models": ["qwen2.5:32b", "qwen2.5-coder:7b"]
      },
      "default_models": [
          "qwen2.5:32b",
          "qwen2.5-coder:7b", 
          "llama3:8b"
      ],
      "system_prompts": {
          "general": "You are a helpful and concise informational assistant. Provide clear, accurate, and direct answers to the user's questions.",
          "coding": "You are an expert software developer and code assistant. Your role is to provide clean, efficient, and well-explained code. When asked to write code, provide only the code block. When asked to review or explain, be thorough."
      },
      "security": {
          "allowed_read_paths": [
              "~/.config/ai",
              "~/Documents", 
              "~/Downloads",
              "."
          ],
          "allowed_write_paths": [
              "~/Documents",
              "~/Downloads", 
              "./output"
          ]
      }
  }
  
  # Remove cloud-related configuration options
  # Simplify load_config() function to focus on local-only setup
  ```

#### Update Configuration Models
- [ ] Edit `ai/models.py`:
  ```python
  class ConfigModel(BaseModel):
      """Simplified configuration model."""
      ollama: Dict[str, Any] = Field(default_factory=dict)
      default_models: List[str] = Field(default_factory=list)
      task_models: Optional[Dict[str, List[str]]] = None  # Advanced mode trigger
      system_prompts: Dict[str, str] = Field(default_factory=dict)
      security: Dict[str, Any] = Field(default_factory=dict)
      
      # Remove all cloud-related fields
  ```

### Day 11-12: CLI Transformation with Proper Subparsers

#### Create New CLI Structure with Standard Subcommands
- [ ] Backup current CLI: `cp ai/cli.py ai/cli-old.py`
- [ ] Rewrite `ai/cli.py` with proper subparser structure:
  ```python
  #!/usr/bin/env python3
  """Simplified CLI for local-first AI with proper subcommand structure."""
  
  import sys
  import argparse
  import asyncio
  from rich.console import Console
  from rich.panel import Panel
  
  console = Console()
  
  def create_parser():
      """Create argument parser with proper subcommand structure."""
      parser = argparse.ArgumentParser(
          description="AI Library - Local-First AI",
          prog="ai"
      )
      
      # Global flags (work with any command)
      parser.add_argument("--verbose", "-v", action="store_true",
                         help="Show detailed information")
      
      # Create subparsers for commands
      subparsers = parser.add_subparsers(dest="command", title="Commands", help="Available commands")
      
      # Default ask command (when no subcommand given)
      ask_parser = subparsers.add_parser("ask", help="Ask a question (default)")
      ask_parser.add_argument("prompt", nargs="*", help="Your question")
      ask_parser.add_argument("--code", "-c", action="store_true",
                             help="Use coding model and optimized prompts")
      ask_parser.add_argument("--offline", action="store_true",
                             help="Force offline-only operation (default)")
      ask_parser.add_argument("--privacy", action="store_true",
                             help="Alias for --offline")
      ask_parser.add_argument("--stream", action="store_true",
                             help="Stream response tokens")
      ask_parser.add_argument("--model", "-m", help="Specific model to use")
      ask_parser.add_argument("--system", "-s", help="System prompt")
      
      # Model management commands
      models_parser = subparsers.add_parser("models", help="Manage local models")
      models_subparsers = models_parser.add_subparsers(dest="models_command", title="Model commands")
      
      # models list
      models_subparsers.add_parser("list", help="List available local models")
      
      # models pull
      pull_parser = models_subparsers.add_parser("pull", help="Pull/download a model")
      pull_parser.add_argument("model_name", help="Name of the model to pull")
      
      # models remove
      remove_parser = models_subparsers.add_parser("remove", help="Remove a model")
      remove_parser.add_argument("model_name", help="Name of the model to remove")
      
      # Setup command
      subparsers.add_parser("setup", help="Run interactive setup wizard")
      
      # Migration command
      subparsers.add_parser("migrate-from-llm", help="Migrate from LLM directory")
      
      # Status command
      subparsers.add_parser("status", help="Show system status")
      
      return parser
  
  def parse_args_with_defaults(parser):
      """Parse args with smart defaults for backward compatibility."""
      # If no arguments provided, show help
      if len(sys.argv) == 1:
          parser.print_help()
          sys.exit(0)
      
      # If first arg doesn't look like a subcommand, treat as ask
      if (len(sys.argv) > 1 and 
          not sys.argv[1].startswith('-') and 
          sys.argv[1] not in ['models', 'setup', 'migrate-from-llm', 'status']):
          # Insert 'ask' as the command
          sys.argv.insert(1, 'ask')
      
      return parser.parse_args()
  
  async def main_async():
      """Main async CLI entry point."""
      parser = create_parser()
      args = parse_args_with_defaults(parser)
      
      # Handle subcommands
      if args.command == "ask" or args.command is None:
          return await handle_ask_command(args)
      elif args.command == "models":
          return await handle_models_command(args)
      elif args.command == "setup":
          from .setup import run_setup_wizard
          return await run_setup_wizard()
      elif args.command == "migrate-from-llm":
          from .migration import run_llm_migration
          return run_llm_migration()  # This one stays sync
      elif args.command == "status":
          return await show_status()
      else:
          parser.print_help()
          return 1
  
  def main():
      """Main CLI entry point with single async event loop."""
      try:
          return asyncio.run(main_async())
      except KeyboardInterrupt:
          console.print("\n❌ Operation cancelled by user.")
          return 1
      except Exception as e:
          console.print(f"❌ [red]Unexpected error: {e}[/red]")
          return 1
  
  async def handle_ask_command(args):
      """Handle the main ask functionality."""
      if not args.prompt:
          console.print("❌ No prompt provided. Usage: ai 'your question'")
          return 1
      
      prompt = " ".join(args.prompt)
      
      # Determine task type
      task_type = "coding" if args.code else "general"
      
      # Import and use the main API
      from .api import ask_async, stream_async
      
      try:
          if args.stream:
              async for chunk in stream_async(prompt, task_type=task_type, model=args.model, system=args.system):
                  console.print(chunk, end="")
              console.print()  # Final newline
          else:
              response = await ask_async(prompt, task_type=task_type, model=args.model, system=args.system)
              console.print(response)
              
              if args.verbose:
                  console.print(f"\n[dim]Model: {response.model} | Time: {response.time:.2f}s[/dim]")
      
      except Exception as e:
          console.print(f"❌ [red]Error: {e}[/red]")
          return 1
      
      return 0
  
  async def handle_models_command(args):
      """Handle model management commands."""
      if not args.models_command:
          console.print("Usage: ai models [list|pull|remove] [model-name]")
          return 1
      
      if args.models_command == "list":
          from .models_manager import list_available_models
          return await list_available_models()
      
      elif args.models_command == "pull":
          from .models_manager import pull_model_with_progress
          return await pull_model_with_progress(args.model_name)
      
      elif args.models_command == "remove":
          from .models_manager import remove_model
          return await remove_model(args.model_name)
      
      return 1
  ```

### Day 13: Create Setup Wizard

#### Create Setup Module
- [ ] Create `ai/setup.py`:
  ```python
  import asyncio
  from pathlib import Path
  from rich.console import Console
  from rich.progress import Progress, SpinnerColumn, TextColumn
  from rich.prompt import Confirm
  
  console = Console()
  
  async def run_setup_wizard():
      """Interactive setup with transparent explanations."""
      console.print("[bold blue]Welcome to the AI setup wizard![/bold blue]")
      console.print("This will configure your local AI environment step by step.")
      console.print()
      
      # Step 1: Check Ollama
      console.print("🔎 [bold]Step 1:[/bold] Checking for Ollama...")
      with console.status("[bold green]Checking Ollama status..."):
          ollama_available = await check_ollama_available()
      
      if not ollama_available:
          console.print("❌ [red]Ollama not found or not running.[/red]")
          console.print("📋 Please install Ollama from: https://ollama.ai/")
          console.print("   Then start it and run 'ai setup' again.")
          return False
      
      console.print("✅ [green]Ollama found and running.[/green]")
      console.print(f"   Connected to: http://localhost:11434")
      
      # Step 2: Check and install models
      console.print("\n🧠 [bold]Step 2:[/bold] Setting up AI models...")
      models_status = await check_models_status()
      
      recommended_models = {
          "qwen2.5:32b": {"size": "~20GB", "purpose": "General questions, best overall model"},
          "qwen2.5-coder:7b": {"size": "~5GB", "purpose": "Coding assistance, faster inference"}
      }
      
      for model, info in recommended_models.items():
          if not models_status.get(model, {}).get("available", False):
              console.print(f"\n📦 Model: [bold]{model}[/bold]")
              console.print(f"   Purpose: {info['purpose']}")
              console.print(f"   Size: {info['size']}")
              
              if Confirm.ask(f"   Download {model}?", default=True):
                  await pull_model_with_progress(model)
              else:
                  console.print(f"   ⏭️  Skipped {model}")
      
      # Step 3: Create configuration
      console.print("\n📝 [bold]Step 3:[/bold] Creating configuration...")
      config_path = create_default_config()
      console.print(f"   ✅ Configuration saved to: [green]{config_path}[/green]")
      console.print("   📂 Safe file access configured for:")
      console.print("      • Current directory and subdirectories")
      console.print("      • ~/Documents and ~/Downloads")
      console.print("   🔧 You can customize this in the config file")
      
      # Step 4: LLM compatibility
      console.print(f"\n🔗 [bold]Step 4:[/bold] Backward compatibility...")
      if Confirm.ask("Create 'llm' command alias for backward compatibility?", default=True):
          create_llm_alias()
          console.print("   ✅ Alias 'llm' created. You can now use 'llm' just like before.")
      else:
          console.print("   ⏭️  Skipped alias creation")
      
      # Success message
      console.print("\n🎉 [bold green]Setup complete![/bold green]")
      console.print("\n💡 [bold]Try these commands:[/bold]")
      console.print("   [yellow]ai 'Hello, world!'[/yellow]           # General question")
      console.print("   [yellow]ai 'Write a function' --code[/yellow]  # Coding assistance")
      console.print("   [yellow]ai models list[/yellow]              # See available models")
      console.print("   [yellow]ai status[/yellow]                   # Check system status")
      
      return True
  
  async def check_ollama_available():
      """Check if Ollama is running."""
      try:
          import httpx
          async with httpx.AsyncClient(timeout=5) as client:
              response = await client.get("http://localhost:11434/api/tags")
              return response.status_code == 200
      except:
          return False
  
  async def check_models_status():
      """Check status of recommended models."""
      try:
          from .backends.local import LocalBackend
          backend = LocalBackend()
          available_models = await backend.models()
          
          return {
              "qwen2.5:32b": {"available": "qwen2.5:32b" in available_models},
              "qwen2.5-coder:7b": {"available": "qwen2.5-coder:7b" in available_models}
          }
      except:
          return {}
  
  def create_default_config():
      """Create default configuration file."""
      from .config import DEFAULT_CONFIG
      import yaml
      
      config_dir = Path.home() / ".config" / "ai"
      config_dir.mkdir(parents=True, exist_ok=True)
      config_path = config_dir / "config.yaml"
      
      with open(config_path, 'w') as f:
          yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, indent=2)
      
      return config_path
  
  def create_llm_alias():
      """Create cross-platform LLM compatibility."""
      import platform
      
      if platform.system() == "Windows":
          create_windows_llm_alias()
      else:
          create_unix_llm_alias()
  
  def create_unix_llm_alias():
      """Create bash/zsh compatible alias."""
      script_content = '''#!/bin/bash
  # LLM compatibility wrapper - maps to AI with offline mode
  exec ai ask "$@" --offline
  '''
      
      bin_dir = Path.home() / ".local" / "bin"
      bin_dir.mkdir(parents=True, exist_ok=True)
      
      alias_path = bin_dir / "llm"
      alias_path.write_text(script_content)
      alias_path.chmod(0o755)
  
  def create_windows_llm_alias():
      """Create Windows batch file alias."""
      script_content = '''@echo off
  REM LLM compatibility wrapper for Windows
  ai ask %* --offline
  '''
      
      # Try to find a directory in PATH for the alias
      import os
      for path_dir in os.environ.get("PATH", "").split(os.pathsep):
          if path_dir and Path(path_dir).exists() and os.access(path_dir, os.W_OK):
              alias_path = Path(path_dir) / "llm.bat"
              alias_path.write_text(script_content)
              return
      
      # Fallback: create in user directory and warn prominently
      user_dir = Path.home()
      alias_path = user_dir / "llm.bat"
      alias_path.write_text(script_content)
      console.print(f"   ⚠️  [yellow]Created {alias_path}[/yellow]")
      console.print()
      console.print("   [bold red]IMPORTANT:[/bold red] To use 'llm' from anywhere, add this to your PATH:")
      console.print(f"   [bold blue]{user_dir}[/bold blue]")
      console.print()
      console.print("   🔧 [dim]How to add to PATH on Windows:[/dim]")
      console.print("      1. Press Win+R, type 'sysdm.cpl', press Enter")
      console.print("      2. Click 'Environment Variables...'")
      console.print("      3. Under 'User variables', select 'Path', click 'Edit...'")
      console.print(f"      4. Click 'New', add: {user_dir}")
      console.print("      5. Click 'OK' on all dialogs")
      console.print("      6. Restart your command prompt")
  ```

### Day 14: Create Model Manager

#### Create Models Manager Module
- [ ] Create `ai/models_manager.py`:
  ```python
  import asyncio
  import json
  from typing import Dict, List
  import httpx
  from rich.console import Console
  from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
  from rich.table import Table
  
  console = Console()
  
  class ModelManager:
      def __init__(self, base_url: str = "http://localhost:11434"):
          self.base_url = base_url
      
      async def list_available_models(self) -> List[str]:
          """List models available in Ollama."""
          try:
              async with httpx.AsyncClient(timeout=10) as client:
                  response = await client.get(f"{self.base_url}/api/tags")
                  data = response.json()
                  return [model["name"] for model in data.get("models", [])]
          except Exception as e:
              console.print(f"❌ Error listing models: {e}")
              return []
      
      async def pull_model_with_progress(self, model_name: str) -> bool:
          """Pull model with progress tracking."""
          console.print(f"📥 Pulling model: [bold]{model_name}[/bold]")
          console.print("   This may take several minutes depending on model size...")
          
          try:
              async with httpx.AsyncClient(timeout=1800) as client:  # 30 min timeout
                  async with client.stream(
                      "POST", 
                      f"{self.base_url}/api/pull",
                      json={"name": model_name}
                  ) as response:
                      response.raise_for_status()
                      
                      with Progress(
                          TextColumn("[progress.description]{task.description}"),
                          BarColumn(),
                          TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                          TimeElapsedColumn(),
                          console=console
                      ) as progress:
                          task = progress.add_task(f"Downloading {model_name}...", total=100)
                          last_percent = 0
                          
                          async for line in response.aiter_lines():
                              if line:
                                  try:
                                      data = json.loads(line)
                                      if "total" in data and "completed" in data and data["total"] > 0:
                                          total = data["total"]
                                          completed = data["completed"]
                                          percentage = (completed / total) * 100
                                          progress.update(task, completed=percentage)
                                          last_percent = percentage
                                      elif "status" in data:
                                          if "downloading" in data["status"].lower():
                                              progress.update(task, description=f"Downloading {model_name}...")
                                          elif "verifying" in data["status"].lower():
                                              progress.update(task, description=f"Verifying {model_name}...")
                                  except json.JSONDecodeError:
                                      pass
              
              console.print(f"✅ [green]Successfully pulled: {model_name}[/green]")
              return True
              
          except Exception as e:
              console.print(f"❌ [red]Failed to pull {model_name}: {e}[/red]")
              return False
      
      async def remove_model(self, model_name: str) -> bool:
          """Remove model from Ollama."""
          try:
              async with httpx.AsyncClient(timeout=30) as client:
                  response = await client.delete(
                      f"{self.base_url}/api/delete",
                      json={"name": model_name}
                  )
                  response.raise_for_status()
                  return True
          except Exception as e:
              console.print(f"❌ [red]Failed to remove {model_name}: {e}[/red]")
              return False
  
  # Convenience functions for CLI (return values for compatibility)
  async def list_available_models():
      """CLI function to list models."""
      manager = ModelManager()
      models = await manager.list_available_models()
      
      if models:
          table = Table(title="Available Local Models")
          table.add_column("Model Name", style="cyan")
          table.add_column("Type", style="green")
          
          for model in sorted(models):
              model_type = "Coding" if "cod" in model.lower() else "General"
              table.add_row(model, model_type)
          
          console.print(table)
          console.print(f"\n💡 Found {len(models)} models")
      else:
          console.print("📭 No models found.")
          console.print("💡 Run 'ai setup' to install recommended models")
          console.print("   Or manually pull a model: 'ai models pull llama2'")
      
      return 0 if models else 1
  
  async def pull_model_with_progress(model_name: str):
      """CLI function to pull a model."""
      manager = ModelManager()
      success = await manager.pull_model_with_progress(model_name)
      return 0 if success else 1
  
  async def remove_model(model_name: str):
      """CLI function to remove a model."""
      manager = ModelManager()
      
      # Confirm deletion
      from rich.prompt import Confirm
      if not Confirm.ask(f"Really remove model '{model_name}'?"):
          console.print("❌ Cancelled")
          return 1
      
      success = await manager.remove_model(model_name)
      if success:
          console.print(f"✅ [green]Successfully removed: {model_name}[/green]")
      
      return 0 if success else 1
  ```

---

## Phase 3: Migration & Compatibility (Week 3)

### Day 15-16: LLM Migration Tool

#### Create Migration Module
- [ ] Create `ai/migration.py`:
  ```python
  import os
  import shutil
  from pathlib import Path
  from rich.console import Console
  from rich.table import Table
  from rich.panel import Panel
  
  console = Console()
  
  def run_llm_migration():
      """Complete migration from LLM directory."""
      console.print(Panel.fit(
          "[bold blue]Migrating from LLM directory...[/bold blue]",
          title="🔄 Migration Tool"
      ))
      console.print()
      
      # Step 1: Check for existing LLM installation
      llm_path = shutil.which("llm")
      if llm_path:
          console.print(f"✅ Found existing LLM command at: [green]{llm_path}[/green]")
      else:
          console.print("ℹ️  No existing LLM command found (this is fine)")
      
      # Step 2: Check for LLM models in Ollama
      models_status = check_llm_models()
      
      if models_status["qwen_models_available"]:
          console.print("✅ Qwen models already available in Ollama")
          console.print("   Your existing models will work with the new 'ai' command")
      else:
          console.print("📦 Qwen models not found in Ollama")
          console.print("💡 Run 'ai setup' to install recommended models")
      
      # Step 3: Create compatibility alias
      console.print("\n🔗 Creating backward compatibility...")
      create_llm_alias()
      console.print("✅ Created 'llm' command alias")
      console.print("   You can continue using 'llm' exactly like before")
      
      # Step 4: Show migration examples
      show_migration_guide()
      
      # Step 5: Next steps
      console.print("\n🎯 [bold]Next Steps:[/bold]")
      console.print("1. Test the migration: [yellow]ai 'Hello world!'[/yellow]")
      console.print("2. Test LLM compatibility: [yellow]llm 'Write code' --code[/yellow]")
      console.print("3. Run setup if needed: [yellow]ai setup[/yellow]")
      console.print("4. Check status anytime: [yellow]ai status[/yellow]")
      
      return 0
  
  def check_llm_models():
      """Check if LLM-style models are available."""
      try:
          from .backends.local import LocalBackend
          import asyncio
          
          async def check():
              backend = LocalBackend()
              available_models = await backend.models()
              
              qwen_models = [m for m in available_models if "qwen" in m.lower()]
              return {
                  "qwen_models_available": len(qwen_models) > 0,
                  "qwen_models": qwen_models,
                  "all_models": available_models
              }
          
          return asyncio.run(check())
      except:
          return {"qwen_models_available": False, "qwen_models": [], "all_models": []}
  
  def show_migration_guide():
      """Show migration examples in a table."""
      console.print("\n📚 [bold]Command Migration Guide:[/bold]")
      
      table = Table()
      table.add_column("Old LLM Command", style="red", width=30)
      table.add_column("New AI Command", style="green", width=30)
      table.add_column("Notes", style="yellow", width=25)
      
      examples = [
          ('llm "Hello world"', 'ai "Hello world"', 'Basic usage'),
          ('llm "Write code" --code', 'ai "Write code" --code', 'Coding mode'),
          ('echo "debug" | llm --code', 'echo "debug" | ai --code', 'Pipe support'),
          ('llm "question"', 'llm "question"', 'Alias still works'),
      ]
      
      for old, new, note in examples:
          table.add_row(old, new, note)
      
      console.print(table)
      console.print("\n💡 [dim]The 'llm' alias will continue to work for backward compatibility.[/dim]")
  ```

### Day 17: Integration & API Updates

#### Update Main API to Use Enhanced Backend
- [ ] Edit `ai/api.py`:
  ```python
  def ask(
      prompt: Union[str, List[Union[str, ImageInput]]],
      *,
      model: Optional[str] = None,
      system: Optional[str] = None,
      task_type: Optional[str] = None,  # NEW: for coding vs general
      temperature: Optional[float] = None,
      max_tokens: Optional[int] = None,
      tools: Optional[List] = None,
      **kwargs,
  ) -> AIResponse:
      """Ask with enhanced local backend."""
      backend = LocalBackend()
      
      # Auto-select model if not specified
      if not model:
          inferred_task = task_type or ("coding" if kwargs.get("code") else "general")
          model = asyncio.run(backend.get_optimal_model(inferred_task))
      
      # Auto-select system prompt if not specified
      if not system and task_type:
          config = get_config()
          system = config.system_prompts.get(task_type)
      
      return asyncio.run(backend.ask(
          prompt, 
          model=model, 
          system=system, 
          temperature=temperature,
          max_tokens=max_tokens,
          tools=tools,
          **kwargs
      ))
  
  # Similar updates for stream() function
  ```

#### Add Convenience Functions
- [ ] Add to `ai/__init__.py`:
  ```python
  # Convenience functions for task-specific usage
  def ask_coding(prompt: str, **kwargs) -> AIResponse:
      """Ask with coding-optimized model and prompt."""
      return ask(prompt, task_type="coding", **kwargs)
  
  def ask_general(prompt: str, **kwargs) -> AIResponse:
      """Ask with general-purpose model and prompt."""
      return ask(prompt, task_type="general", **kwargs)
  
  # Update exports (remove cloud-related)
  __all__ = [
      "ask", "stream", "chat", "ask_coding", "ask_general",
      "AIResponse", "LocalBackend", 
      # ... other exports, but NOT CloudBackend
  ]
  ```

---

## Phase 4: Testing & Deployment (Week 3-4)

### Day 18-19: Comprehensive Testing

#### Create Test Suite
- [ ] Test basic functionality:
  ```bash
  # Core functionality tests
  ai "Hello world"                           # Should work with optimal model
  ai "Write a sorting function" --code       # Should use coding model/prompt
  ai setup                                   # Should guide through setup
  ai models list                             # Should show local models
  echo "debug this code" | ai ask --code     # Should work with pipes
  
  # Migration compatibility tests
  llm "Hello world"                          # Should work via alias
  llm "Write code" --code                    # Should work via alias
  
  # Model management tests
  ai models pull qwen2.5:32b                # Should download with progress
  ai models remove test-model               # Should remove model safely
  
  # Security tests
  ai "read file ../../etc/passwd" --tools read_file  # Should be blocked
  ai "write to dangerous location" --tools write_file # Should be blocked
  ```

#### Performance & Security Validation
- [ ] Verify startup time < 500ms
- [ ] Test file operation security
- [ ] Verify no network access from tools
- [ ] Test memory usage is reasonable

### Day 20-21: Documentation & Final Polish

#### Update Documentation
- [ ] Create `UPGRADE_GUIDE.md`:
  ```markdown
  # Upgrade Guide: Enhanced AI Library
  
  ## Quick Start
  1. Run: `ai migrate-from-llm` (if upgrading from LLM)
  2. Run: `ai setup` (for new installations)
  3. Test: `ai 'Hello world!'`
  
  ## New Command Structure
  | Old Style | New Standard Style |
  |-----------|-------------------|
  | `ai --models pull model` | `ai models pull model` |
  | `ai --setup` | `ai setup` |
  
  ## New Features
  - ✅ Proper subcommand structure (`ai models list`)
  - ✅ Cross-platform LLM compatibility
  - ✅ Enhanced security with configurable file access
  - ✅ Interactive setup wizard
  - ✅ Smart model selection
  
  ## Security Improvements
  - 🔒 File operations restricted to safe directories
  - 🔒 No network access or code execution
  - 🔒 Configurable security policies
  ```

#### Remove Legacy Files and Clean Up
- [ ] `rm ai/cli-old.py` (backup CLI)
- [ ] `rm ai-backup/` (if tests pass)
- [ ] `rm IMPLEMENTATION_CHECKLIST.md` (merge into this file)
- [ ] Update `pyproject.toml` version and dependencies
- [ ] Run final tests: `python -m pytest tests/` (if test suite exists)

---

## Rollback Plan

### Emergency Rollback (if critical issues found)
- [ ] `git checkout main`
- [ ] `pip install -e .` to restore old version
- [ ] Test that original functionality works
- [ ] Document what went wrong for future attempts

### Partial Rollback Options
- [ ] Keep new CLI but restore cloud backend (revert Phase 1)
- [ ] Keep enhanced local backend but restore old CLI (revert Phase 2)  
- [ ] Cherry-pick specific improvements without full migration

---

## Success Criteria & Final Validation

### Functional Requirements ✅
- [ ] `ai "question"` works with automatic model selection
- [ ] `ai "code question" --code` uses optimized coding model/prompt
- [ ] `ai setup` provides guided installation
- [ ] `ai models list/pull/remove` manages local models
- [ ] `ai migrate-from-llm` handles transition smoothly
- [ ] Local tools work safely with path validation
- [ ] Cross-platform compatibility (Windows/macOS/Linux)

### Non-Functional Requirements ✅
- [ ] Zero cloud dependencies in final package
- [ ] Clean, professional CLI output with Rich formatting
- [ ] Fast startup time (<500ms)
- [ ] Secure file operations with configurable policies
- [ ] Educational setup process that explains each step
- [ ] No legacy code burden or unused imports

### Compatibility Requirements ✅
- [ ] `llm` alias works for basic usage on all platforms
- [ ] Pipe compatibility: `echo "code" | ai ask --code`
- [ ] Same or better model quality as LLM directory
- [ ] Migration preserves user experience

### Security Requirements ✅
- [ ] File operations restricted to configured safe paths
- [ ] No code execution capabilities
- [ ] No network access from tools
- [ ] Input validation throughout tool system
- [ ] Configuration file controls security policies

---

## Timeline Expectations

**Total Duration**: 3-4 weeks (flexible based on testing needs)

- **Week 1-2**: Infrastructure changes (this is the most complex phase)
- **Week 2-3**: CLI transformation and model management
- **Week 3**: Migration tools and compatibility layer
- **Week 3-4**: Testing, documentation, and deployment

> **Note**: Week 1's infrastructure phase may extend into Week 2 as it involves significant architectural changes. The priority is getting the foundation right rather than rushing to meet deadlines.

---

## Post-Migration Benefits

✅ **Simplified Architecture**: ~40% less code, focused on local-first use cases  
✅ **Enhanced Security**: Configurable file access, no network tools or code execution  
✅ **Better UX**: Standard subcommand structure, educational setup wizard  
✅ **Professional CLI**: Rich terminal output, proper progress tracking  
✅ **Smart Defaults**: Automatic model selection, optimized prompts  
✅ **Cross-Platform**: Works consistently on Windows, macOS, and Linux  
✅ **Migration Ready**: Comprehensive tooling for LLM directory transition  
✅ **Configuration-Driven**: Single source of truth for all model and security settings  
✅ **Clean Async Architecture**: Single event loop with proper exception handling  

## Final Implementation Notes

This plan incorporates peer review feedback for maximum robustness:

1. **Configuration as Single Source of Truth**: The `get_optimal_model()` function reads directly from the loaded configuration, making `config.yaml` the authoritative source for all model selection logic.

2. **Clean Async Architecture**: A single `asyncio.run()` call at the top level with proper exception handling, making the CLI async-consistent throughout.

3. **Enhanced Windows Support**: Comprehensive PATH guidance for Windows users who need to manually add the alias directory, with step-by-step instructions.

This migration transforms the agents directory into a focused, secure, local-first AI tool that surpasses the LLM directory's capabilities while providing a clean, modern codebase and professional user experience.