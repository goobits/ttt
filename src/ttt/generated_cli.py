#!/usr/bin/env python3
"""Auto-generated from goobits.yaml"""
import os
import sys
import importlib.util
from pathlib import Path
import rich_click as click
from rich_click import RichGroup, RichCommand

# Set up rich-click configuration globally
click.rich_click.USE_RICH_MARKUP = True  
click.rich_click.USE_MARKDOWN = False  # Disable markdown to avoid conflicts
click.rich_click.MARKUP_MODE = "rich"

# Environment variables for additional control
os.environ["RICH_CLICK_USE_RICH_MARKUP"] = "1"
os.environ["RICH_CLICK_FORCE_TERMINAL"] = "1"
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "#ff5555"
click.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."
click.rich_click.ERRORS_EPILOGUE = "To find out more, visit https://github.com/anthropics/claude-code"
click.rich_click.MAX_WIDTH = 120  # Set reasonable width
click.rich_click.WIDTH = 120  # Set consistent width
click.rich_click.COLOR_SYSTEM = "auto"
click.rich_click.SHOW_SUBCOMMAND_ALIASES = True
click.rich_click.ALIGN_OPTIONS_SWITCHES = True
click.rich_click.STYLE_OPTION = "#ff79c6"      # Dracula Pink - for option flags
click.rich_click.STYLE_SWITCH = "#50fa7b"      # Dracula Green - for switches
click.rich_click.STYLE_METAVAR = "#8BE9FD not bold"   # Light cyan - for argument types (OPTIONS, COMMAND)  
click.rich_click.STYLE_METAVAR_SEPARATOR = "#6272a4"  # Dracula Comment
click.rich_click.STYLE_HEADER_TEXT = "bold yellow"    # Bold yellow - for section headers
click.rich_click.STYLE_EPILOGUE_TEXT = "#6272a4"      # Dracula Comment
click.rich_click.STYLE_FOOTER_TEXT = "#6272a4"        # Dracula Comment
click.rich_click.STYLE_USAGE = "#BD93F9"              # Purple - for "Usage:" line
click.rich_click.STYLE_USAGE_COMMAND = "bold"         # Bold for main command name
click.rich_click.STYLE_DEPRECATED = "#ff5555"         # Dracula Red
click.rich_click.STYLE_HELPTEXT_FIRST_LINE = "#f8f8f2" # Dracula Foreground
click.rich_click.STYLE_HELPTEXT = "#B3B8C0"           # Light gray - for help descriptions
click.rich_click.STYLE_OPTION_DEFAULT = "#ffb86c"     # Dracula Orange
click.rich_click.STYLE_REQUIRED_SHORT = "#ff5555"     # Dracula Red
click.rich_click.STYLE_REQUIRED_LONG = "#ff5555"      # Dracula Red
click.rich_click.STYLE_OPTIONS_PANEL_BORDER = "dim"   # Dim for subtle borders
click.rich_click.STYLE_COMMANDS_PANEL_BORDER = "dim"  # Dim for subtle borders
click.rich_click.STYLE_COMMAND = "#50fa7b"            # Dracula Green - for command names in list
click.rich_click.STYLE_COMMANDS_TABLE_COLUMN_WIDTH_RATIO = (1, 3)  # Command:Description ratio (1/4 : 3/4)


# Command groups will be set after main function is defined


# Hooks system - try to import app_hooks module
app_hooks = None
try:
    # Try to import from the same directory as this script
    script_dir = Path(__file__).parent
    hooks_path = script_dir / "app_hooks.py"
    
    if hooks_path.exists():
        spec = importlib.util.spec_from_file_location("app_hooks", hooks_path)
        app_hooks = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_hooks)
    else:
        # Try to import from Python path
        import app_hooks
except (ImportError, FileNotFoundError):
    # No hooks module found, use default behavior
    pass

def load_plugins(cli_group):
    """Load plugins from the conventional plugin directory."""
    # Define plugin directories to search
    plugin_dirs = [
        # User-specific plugin directory
        Path.home() / ".config" / "goobits" / "GOOBITS TTT CLI" / "plugins",
        # Local plugin directory (same as script)
        Path(__file__).parent / "plugins",
    ]
    
    for plugin_dir in plugin_dirs:
        if not plugin_dir.exists():
            continue
            
        # Add plugin directory to Python path
        sys.path.insert(0, str(plugin_dir))
        
        # Scan for plugin files
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
                
            plugin_name = plugin_file.stem
            
            try:
                # Import the plugin module
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
                plugin_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin_module)
                
                # Call register_plugin if it exists
                if hasattr(plugin_module, "register_plugin"):
                    plugin_module.register_plugin(cli_group)
                    click.echo(f"Loaded plugin: {plugin_name}", err=True)
            except Exception as e:
                click.echo(f"Failed to load plugin {plugin_name}: {e}", err=True)







def get_version():
    """Get version from pyproject.toml or __init__.py"""
    import re
    
    try:
        # Try to get version from pyproject.toml FIRST (most authoritative)
        toml_path = Path(__file__).parent.parent / "pyproject.toml"
        if toml_path.exists():
            content = toml_path.read_text()
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    except Exception:
        pass
    
    try:
        # Fallback to __init__.py
        init_path = Path(__file__).parent / "__init__.py"
        if init_path.exists():
            content = init_path.read_text()
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    except Exception:
        pass
        
    # Final fallback
    return "1.0.0"


def show_help_json(ctx, param, value):
    """Callback for --help-json option."""
    if not value or ctx.resilient_parsing:
        return
    # The triple quotes are important to correctly handle the multi-line JSON string
    click.echo('''{
  "name": "GOOBITS TTT CLI",
  "version": "1.0.0",
  "display_version": true,
  "tagline": "Talk to Transformer",
  "description": "AI-powered conversations, straight from your command line",
  "icon": "🤖",
  "header_sections": [
    {
      "title": "💡 Quick Start",
      "icon": null,
      "items": [
        {
          "item": "ttt \\"What is the meaning of life?\\"",
          "desc": "Instant response",
          "style": "example"
        },
        {
          "item": "ttt chat",
          "desc": "Interactive session",
          "style": "example"
        },
        {
          "item": "ttt models",
          "desc": "Explore available models",
          "style": "example"
        },
        {
          "item": "ttt config set model gpt-4",
          "desc": "Set your preferred model",
          "style": "example"
        }
      ]
    },
    {
      "title": "🔑 Initial Setup",
      "icon": null,
      "items": [
        {
          "item": "1. See providers",
          "desc": "ttt providers",
          "style": "setup"
        },
        {
          "item": "2. Add API key",
          "desc": "export OPENROUTER_API_KEY='your-key-here'",
          "style": "setup"
        },
        {
          "item": "3. Check setup",
          "desc": "ttt status",
          "style": "setup"
        },
        {
          "item": "4. Start chatting",
          "desc": "ttt chat",
          "style": "setup"
        }
      ]
    }
  ],
  "footer_note": "📚 For detailed help on a command, run: [color(2)]ttt [COMMAND][/color(2)] [#ff79c6]--help[/#ff79c6]",
  "commands": {
    "ask": {
      "desc": "Quickly ask one-off questions",
      "icon": "💬",
      "is_default": true,
      "args": [
        {
          "name": "prompt",
          "desc": "The question or prompt",
          "nargs": "*",
          "choices": null
        }
      ],
      "options": [
        {
          "name": "model",
          "short": "m",
          "type": "str",
          "desc": "LLM model to use",
          "default": null,
          "choices": null
        },
        {
          "name": "temperature",
          "short": "t",
          "type": "float",
          "desc": "Sampling temperature (0.0-2.0)",
          "default": 0.7,
          "choices": null
        },
        {
          "name": "max-tokens",
          "short": null,
          "type": "int",
          "desc": "Maximum response length",
          "default": null,
          "choices": null
        },
        {
          "name": "tools",
          "short": null,
          "type": "bool",
          "desc": "Enable tool usage",
          "default": false,
          "choices": null
        },
        {
          "name": "session",
          "short": "s",
          "type": "str",
          "desc": "Session ID for context",
          "default": null,
          "choices": null
        },
        {
          "name": "stream",
          "short": null,
          "type": "bool",
          "desc": "Stream the response",
          "default": true,
          "choices": null
        },
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "Output response in JSON format",
          "default": null,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "chat": {
      "desc": "Chat interactively with AI",
      "icon": "💬",
      "is_default": false,
      "args": [],
      "options": [
        {
          "name": "model",
          "short": "m",
          "type": "str",
          "desc": "LLM model to use",
          "default": null,
          "choices": null
        },
        {
          "name": "session",
          "short": "s",
          "type": "str",
          "desc": "Session ID to resume or create",
          "default": null,
          "choices": null
        },
        {
          "name": "tools",
          "short": null,
          "type": "bool",
          "desc": "Enable tool usage in chat",
          "default": false,
          "choices": null
        },
        {
          "name": "markdown",
          "short": null,
          "type": "bool",
          "desc": "Render markdown in responses",
          "default": true,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "list": {
      "desc": "See available resources",
      "icon": "📜",
      "is_default": false,
      "args": [
        {
          "name": "resource",
          "desc": "Type of resource to list",
          "nargs": null,
          "choices": [
            "models",
            "sessions",
            "tools"
          ]
        }
      ],
      "options": [
        {
          "name": "format",
          "short": "f",
          "type": "str",
          "desc": "Output format",
          "default": "table",
          "choices": [
            "table",
            "json",
            "yaml"
          ]
        },
        {
          "name": "verbose",
          "short": "v",
          "type": "bool",
          "desc": "Show detailed information",
          "default": false,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "status": {
      "desc": "Verify system and API health",
      "icon": "✅",
      "is_default": false,
      "args": [],
      "options": [
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "Output status in JSON format",
          "default": null,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "models": {
      "desc": "View AI models",
      "icon": "🧠",
      "is_default": false,
      "args": [],
      "options": [
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "Output models in JSON format",
          "default": null,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "info": {
      "desc": "Detailed model information",
      "icon": "ℹ️",
      "is_default": false,
      "args": [
        {
          "name": "model",
          "desc": "Model name",
          "nargs": null,
          "choices": null
        }
      ],
      "options": [
        {
          "name": "json",
          "short": null,
          "type": "flag",
          "desc": "Output model info in JSON format",
          "default": null,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "export": {
      "desc": "Save your chat history",
      "icon": "💾",
      "is_default": false,
      "args": [
        {
          "name": "session",
          "desc": "Session ID to export",
          "nargs": null,
          "choices": null
        }
      ],
      "options": [
        {
          "name": "format",
          "short": "f",
          "type": "str",
          "desc": "Export format",
          "default": "markdown",
          "choices": [
            "markdown",
            "json",
            "txt"
          ]
        },
        {
          "name": "output",
          "short": "o",
          "type": "str",
          "desc": "Output file path",
          "default": null,
          "choices": null
        },
        {
          "name": "include-metadata",
          "short": null,
          "type": "bool",
          "desc": "Include timestamps and model info",
          "default": false,
          "choices": null
        }
      ],
      "subcommands": null
    },
    "config": {
      "desc": "Customize your setup",
      "icon": "⚙️",
      "is_default": false,
      "args": [],
      "options": [],
      "subcommands": {
        "get": {
          "desc": "Get a configuration value",
          "icon": null,
          "is_default": false,
          "args": [
            {
              "name": "key",
              "desc": "Configuration key",
              "nargs": null,
              "choices": null
            }
          ],
          "options": [],
          "subcommands": null
        },
        "set": {
          "desc": "Set a configuration value",
          "icon": null,
          "is_default": false,
          "args": [
            {
              "name": "key",
              "desc": "Configuration key",
              "nargs": null,
              "choices": null
            },
            {
              "name": "value",
              "desc": "Configuration value",
              "nargs": null,
              "choices": null
            }
          ],
          "options": [],
          "subcommands": null
        },
        "list": {
          "desc": "List all configuration",
          "icon": null,
          "is_default": false,
          "args": [],
          "options": [
            {
              "name": "show-secrets",
              "short": null,
              "type": "bool",
              "desc": "Include API keys in output",
              "default": false,
              "choices": null
            }
          ],
          "subcommands": null
        }
      }
    },
    "tools": {
      "desc": "Manage CLI tools and extensions",
      "icon": "🛠️",
      "is_default": false,
      "args": [],
      "options": [],
      "subcommands": {
        "enable": {
          "desc": "Enable a tool",
          "icon": null,
          "is_default": false,
          "args": [
            {
              "name": "tool_name",
              "desc": "Name of the tool to enable",
              "nargs": null,
              "choices": null
            }
          ],
          "options": [],
          "subcommands": null
        },
        "disable": {
          "desc": "Disable a tool",
          "icon": null,
          "is_default": false,
          "args": [
            {
              "name": "tool_name",
              "desc": "Name of the tool to disable",
              "nargs": null,
              "choices": null
            }
          ],
          "options": [],
          "subcommands": null
        },
        "list": {
          "desc": "List all tools",
          "icon": null,
          "is_default": false,
          "args": [],
          "options": [
            {
              "name": "show-disabled",
              "short": null,
              "type": "bool",
              "desc": "Include disabled tools",
              "default": false,
              "choices": null
            }
          ],
          "subcommands": null
        }
      }
    }
  },
  "command_groups": [
    {
      "name": "Core Commands",
      "commands": [
        "ask",
        "chat",
        "list",
        "status"
      ],
      "icon": null
    },
    {
      "name": "Model Management",
      "commands": [
        "models",
        "info"
      ],
      "icon": null
    },
    {
      "name": "Configuration",
      "commands": [
        "config",
        "tools"
      ],
      "icon": null
    },
    {
      "name": "Data Management",
      "commands": [
        "export"
      ],
      "icon": null
    }
  ],
  "config": {
    "rich_help_panel": true,
    "show_metavars_column": false,
    "append_metavars_help": true,
    "style_errors_suggestion": true,
    "max_width": 120
  },
  "enable_recursive_help": true,
  "enable_help_json": true
}''')
    ctx.exit()





  
    
  

  

  

  

  

  

  

  

  



class DefaultGroup(RichGroup):
    """Allow a default command to be invoked without being specified."""
    
    def __init__(self, *args, default=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_command = default
    
    def resolve_command(self, ctx, args):
        try:
            # Try normal command resolution first
            return super().resolve_command(ctx, args)
        except click.UsageError:
            # If no command found and we have a default, use it
            if self.default_command and args and not any(arg in ['--help-all', '--help-json'] for arg in args):
                # Get the default command object
                cmd = self.commands.get(self.default_command)
                if cmd:
                    # Return command name, command object, and all args
                    return self.default_command, cmd, args
            raise



@click.group(cls=DefaultGroup, default='ask', context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 120})

@click.version_option(version=get_version(), prog_name="GOOBITS TTT CLI")
@click.pass_context

@click.option('--help-json', is_flag=True, callback=show_help_json, is_eager=True, help='Output CLI structure as JSON.', hidden=True)


@click.option('--help-all', is_flag=True, is_eager=True, help='Show help for all commands.', hidden=True)

def main(ctx, help_all=False):
    """🤖 [bold color(6)]GOOBITS TTT CLI v1.0.0[/bold color(6)] - Talk to Transformer

    
    \b
    [#B3B8C0]AI-powered conversations, straight from your command line[/#B3B8C0]
    

    
    \b
    [bold yellow]💡 Quick Start:[/bold yellow]
    [green]ttt "What is the meaning of life?"  [/green] [italic][#B3B8C0]# Instant response[/#B3B8C0][/italic]
    [green]ttt chat                            [/green] [italic][#B3B8C0]# Interactive session[/#B3B8C0][/italic]
    [green]ttt models                          [/green] [italic][#B3B8C0]# Explore available models[/#B3B8C0][/italic]
    [green]ttt config set model gpt-4          [/green] [italic][#B3B8C0]# Set your preferred model[/#B3B8C0][/italic]
    
    \b
    [bold yellow]🔑 Initial Setup:[/bold yellow]
    1. See providers:  [green]ttt providers[/green]
    2. Add API key:    [green]export OPENROUTER_API_KEY='your-key-here'[/green]
    3. Check setup:    [green]ttt status[/green]
    4. Start chatting: [green]ttt chat[/green]
    
    \b
    
       [#B3B8C0]📚 For detailed help on a command, run: [color(2)]ttt [COMMAND][/color(2)] [#ff79c6]--help[/#ff79c6][/#B3B8C0]
    """

    
    if help_all:
        # Print main help
        click.echo(ctx.get_help())
        click.echo() # Add a blank line for spacing

        # Get a list of all command names
        commands_to_show = sorted(ctx.command.list_commands(ctx))

        for cmd_name in commands_to_show:
            command = ctx.command.get_command(ctx, cmd_name)

            # Create a new context for the subcommand
            sub_ctx = click.Context(command, info_name=cmd_name, parent=ctx)

            # Print a separator and the subcommand's help
            click.echo("="*20 + f" HELP FOR: {cmd_name} " + "="*20)
            click.echo(sub_ctx.get_help())
            click.echo() # Add a blank line for spacing

        # Exit after printing all help
        ctx.exit()
    

    pass


# Set command groups after main function is defined
click.rich_click.COMMAND_GROUPS = {
    "main": [
        
        {
            "name": "Core Commands",
            "commands": ['ask', 'chat', 'list', 'status'],
        },
        
        {
            "name": "Model Management",
            "commands": ['models', 'info'],
        },
        
        {
            "name": "Configuration",
            "commands": ['config', 'tools'],
        },
        
        {
            "name": "Data Management",
            "commands": ['export'],
        },
        
    ]
}




@main.command()

@click.argument(
    "PROMPT",
    nargs=-1
)


@click.option("-m", "--model",
    type=str,
    help="LLM model to use"
)

@click.option("-t", "--temperature",
    type=float,
    default=0.7,
    help="Sampling temperature (0.0-2.0)"
)

@click.option("--max-tokens",
    type=int,
    help="Maximum response length"
)

@click.option("--tools",
    type=bool,
    default=False,
    help="Enable tool usage"
)

@click.option("-s", "--session",
    type=str,
    help="Session ID for context"
)

@click.option("--stream",
    type=bool,
    default=True,
    help="Stream the response"
)

@click.option("--json",
    is_flag=True,
    help="Output response in JSON format"
)

def ask(prompt, model, temperature, max_tokens, tools, session, stream, json):
    """💬 Quickly ask one-off questions"""
    # Check if hook function exists
    hook_name = f"on_ask"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(prompt, model, temperature, max_tokens, tools, session, stream, json)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing ask command...")
        
        
        click.echo(f"  prompt: {prompt}")
        
        
        
        
        click.echo(f"  model: {model}")
        
        click.echo(f"  temperature: {temperature}")
        
        click.echo(f"  max-tokens: {max_tokens}")
        
        click.echo(f"  tools: {tools}")
        
        click.echo(f"  session: {session}")
        
        click.echo(f"  stream: {stream}")
        
        click.echo(f"  json: {json}")
        
        




@main.command()


@click.option("-m", "--model",
    type=str,
    help="LLM model to use"
)

@click.option("-s", "--session",
    type=str,
    help="Session ID to resume or create"
)

@click.option("--tools",
    type=bool,
    default=False,
    help="Enable tool usage in chat"
)

@click.option("--markdown",
    type=bool,
    default=True,
    help="Render markdown in responses"
)

def chat(model, session, tools, markdown):
    """💬 Chat interactively with AI"""
    # Check if hook function exists
    hook_name = f"on_chat"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(model, session, tools, markdown)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing chat command...")
        
        
        
        click.echo(f"  model: {model}")
        
        click.echo(f"  session: {session}")
        
        click.echo(f"  tools: {tools}")
        
        click.echo(f"  markdown: {markdown}")
        
        




@main.command()

@click.argument(
    "RESOURCE",
    type=click.Choice(['models', 'sessions', 'tools'])
)


@click.option("-f", "--format",
    type=click.Choice(['table', 'json', 'yaml']),
    default="table",
    help="Output format"
)

@click.option("-v", "--verbose",
    type=bool,
    default=False,
    help="Show detailed information"
)

def list(resource, format, verbose):
    """📜 See available resources"""
    # Check if hook function exists
    hook_name = f"on_list"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(resource, format, verbose)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing list command...")
        
        
        click.echo(f"  resource: {resource}")
        
        
        
        
        click.echo(f"  format: {format}")
        
        click.echo(f"  verbose: {verbose}")
        
        




@main.command()


@click.option("--json",
    is_flag=True,
    help="Output status in JSON format"
)

def status(json):
    """✅ Verify system and API health"""
    # Check if hook function exists
    hook_name = f"on_status"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(json)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing status command...")
        
        
        
        click.echo(f"  json: {json}")
        
        




@main.command()


@click.option("--json",
    is_flag=True,
    help="Output models in JSON format"
)

def models(json):
    """🧠 View AI models"""
    # Check if hook function exists
    hook_name = f"on_models"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(json)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing models command...")
        
        
        
        click.echo(f"  json: {json}")
        
        




@main.command()

@click.argument(
    "MODEL"
)


@click.option("--json",
    is_flag=True,
    help="Output model info in JSON format"
)

def info(model, json):
    """ℹ️  Detailed model information"""
    # Check if hook function exists
    hook_name = f"on_info"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(model, json)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing info command...")
        
        
        click.echo(f"  model: {model}")
        
        
        
        
        click.echo(f"  json: {json}")
        
        




@main.command()

@click.argument(
    "SESSION"
)


@click.option("-f", "--format",
    type=click.Choice(['markdown', 'json', 'txt']),
    default="markdown",
    help="Export format"
)

@click.option("-o", "--output",
    type=str,
    help="Output file path"
)

@click.option("--include-metadata",
    type=bool,
    default=False,
    help="Include timestamps and model info"
)

def export(session, format, output, include_metadata):
    """💾 Save your chat history"""
    # Check if hook function exists
    hook_name = f"on_export"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(session, format, output, include_metadata)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing export command...")
        
        
        click.echo(f"  session: {session}")
        
        
        
        
        click.echo(f"  format: {format}")
        
        click.echo(f"  output: {output}")
        
        click.echo(f"  include-metadata: {include_metadata}")
        
        




@main.group()
def config():
    """⚙️  Customize your setup"""
    pass


@config.command()

@click.argument(
    "KEY"
)


def get(key):
    """Get a configuration value"""
    # Check if hook function exists
    hook_name = f"on_config_get"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(key)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing get command...")
        
        
        click.echo(f"  key: {key}")
        
        
        

@config.command()

@click.argument(
    "KEY"
)

@click.argument(
    "VALUE"
)


def set(key, value):
    """Set a configuration value"""
    # Check if hook function exists
    hook_name = f"on_config_set"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(key, value)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing set command...")
        
        
        click.echo(f"  key: {key}")
        
        click.echo(f"  value: {value}")
        
        
        

@config.command()


@click.option("--show-secrets",
    type=bool,
    default=False,
    help="Include API keys in output"
)

def list(show_secrets):
    """List all configuration"""
    # Check if hook function exists
    hook_name = f"on_config_list"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(show_secrets)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing list command...")
        
        
        
        click.echo(f"  show-secrets: {show_secrets}")
        
        





@main.group()
def tools():
    """🛠️  Manage CLI tools and extensions"""
    pass


@tools.command()

@click.argument(
    "TOOL_NAME"
)


def enable(tool_name):
    """Enable a tool"""
    # Check if hook function exists
    hook_name = f"on_tools_enable"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(tool_name)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing enable command...")
        
        
        click.echo(f"  tool_name: {tool_name}")
        
        
        

@tools.command()

@click.argument(
    "TOOL_NAME"
)


def disable(tool_name):
    """Disable a tool"""
    # Check if hook function exists
    hook_name = f"on_tools_disable"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(tool_name)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing disable command...")
        
        
        click.echo(f"  tool_name: {tool_name}")
        
        
        

@tools.command()


@click.option("--show-disabled",
    type=bool,
    default=False,
    help="Include disabled tools"
)

def list(show_disabled):
    """List all tools"""
    # Check if hook function exists
    hook_name = f"on_tools_list"
    if app_hooks and hasattr(app_hooks, hook_name):
        # Call the hook with all parameters
        hook_func = getattr(app_hooks, hook_name)
        
        result = hook_func(show_disabled)
        
        return result
    else:
        # Default placeholder behavior
        click.echo(f"Executing list command...")
        
        
        
        click.echo(f"  show-disabled: {show_disabled}")
        
        





def cli_entry():
    """Entry point for the CLI when installed via pipx."""
    # Load plugins before running the CLI
    load_plugins(main)
    main()

if __name__ == "__main__":
    cli_entry()
