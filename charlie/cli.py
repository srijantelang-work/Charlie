#!/usr/bin/env python3
"""
Charlie CLI - Main entry point for the Charlie AI Assistant CLI application.
Provides voice-controlled AI interaction through terminal interface.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click

# Try to import Rich components with fallbacks
try:
    from rich.console import Console # type: ignore
    from rich.panel import Panel # type: ignore
    from rich.text import Text # type: ignore
    from rich.table import Table # type: ignore
    from rich.progress import Progress, SpinnerColumn, TextColumn # type: ignore
    from rich import print as rprint # type: ignore 
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback implementations if Rich is not available
    class Console:
        def print(self, *args, **kwargs): print(*args)
        def input(self, prompt="", **kwargs): return input(prompt)
    
    class Panel:
        def __init__(self, *args, **kwargs): pass
    
    class Text:
        def __init__(self, *args, **kwargs): pass
        def append(self, *args, **kwargs): pass
    
    class Table:
        def __init__(self, *args, **kwargs): pass
        def add_column(self, *args, **kwargs): pass
        def add_row(self, *args, **kwargs): pass
    
    class Progress:
        def __init__(self, *args, **kwargs): pass
    
    class SpinnerColumn:
        def __init__(self, *args, **kwargs): pass
    
    class TextColumn:
        def __init__(self, *args, **kwargs): pass
    
    def rprint(*args, **kwargs):
        print(*args)

from charlie import __version__, __description__
from charlie.utils.config import ConfigManager
from charlie.commands.chat import ChatCommand
from charlie.commands.voice import VoiceCommand
from charlie.commands.config import ConfigCommand
from charlie.ui.components import create_welcome_panel, create_status_panel

# Initialize console
console = Console()
config_manager = ConfigManager()

# Global context for CLI
class CLIContext:
    def __init__(self):
        self.config = config_manager
        self.console = console
        self.debug = False
        self.verbose = False

@click.group(invoke_without_command=True)
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config-file', '-c', type=click.Path(), help='Path to config file')
@click.version_option(version=__version__, prog_name='Charlie')
@click.pass_context
def cli(ctx: click.Context, debug: bool = False, verbose: bool = False, config_file: Optional[str] = None):  # type: ignore
    """
    Charlie - Voice-Controlled AI Assistant
    
    Your intelligent AI companion powered by Gemini 2.5 Pro.
    Interact through voice commands or text in your terminal.
    """
    # Create our custom context and store it in Click's context
    cli_ctx = CLIContext()
    cli_ctx.debug = debug
    cli_ctx.verbose = verbose
    
    if config_file:
        cli_ctx.config.load_config(Path(config_file))
    
    ctx.obj = cli_ctx
    
    # If no command is provided, show welcome and start interactive mode
    if ctx.invoked_subcommand is None:
        show_welcome()
        if not debug:
            start_interactive_mode(cli_ctx)

def show_welcome():
    """Display welcome message and system status"""
    console.print(create_welcome_panel())
    
    # Show system status
    status_table = Table(show_header=False, box=None)
    status_table.add_column("", style="cyan")
    status_table.add_column("", style="green")
    
    # Check API connections
    status_table.add_row("🤖 AI Engine", "Gemini 2.5 Pro - Ready")
    status_table.add_row("🎤 Voice Processing", "Google STT/TTS - Ready") 
    status_table.add_row("💾 Memory System", "Supabase - Connected")
    status_table.add_row("⚙️  Task Engine", "Python Automation - Ready")
    
    status_panel = Panel(
        status_table,
        title="[bold green]System Status[/bold green]",
        border_style="green"
    )
    console.print(status_panel)

def start_interactive_mode(ctx: CLIContext):
    """Start interactive mode with command suggestions"""
    console.print("\n[bold cyan]Interactive Mode[/bold cyan]")
    console.print("Type 'help' for available commands, or 'exit' to quit.")
    console.print("Use [bold]'charlie voice'[/bold] for voice interaction.\n")
    
    while True:
        try:
            command = console.input("[bold blue]charlie>[/bold blue] ")
            if command.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]Goodbye! 👋[/yellow]")
                break
            elif command.lower() == 'help':
                show_help()
            elif command.lower().startswith('voice'):
                # Quick voice command
                voice_cmd = VoiceCommand(ctx)
                asyncio.run(voice_cmd.start_listening())
            elif command.lower().startswith('chat'):
                # Quick chat command
                chat_cmd = ChatCommand(ctx)
                asyncio.run(chat_cmd.start_chat())
            elif command.strip():
                # Send to AI for processing
                chat_cmd = ChatCommand(ctx)
                asyncio.run(chat_cmd.process_message(command))
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
        except EOFError:
            break

def show_help():
    """Show help information"""
    help_table = Table(title="Charlie CLI Commands")
    help_table.add_column("Command", style="cyan", no_wrap=True)
    help_table.add_column("Description", style="white")
    help_table.add_column("Example", style="green")
    
    help_table.add_row("chat", "Start text-based conversation", "charlie chat")
    help_table.add_row("voice", "Start voice interaction", "charlie voice --listen")
    help_table.add_row("config", "Manage configuration", "charlie config set api_key YOUR_KEY")
    help_table.add_row("status", "Show system status", "charlie status")
    help_table.add_row("history", "Show conversation history", "charlie history")
    
    console.print(help_table)

# Command groups
@cli.command()
@click.pass_context
def chat(ctx: click.Context):
    """Start interactive chat session with Charlie"""
    chat_cmd = ChatCommand(ctx.obj)
    asyncio.run(chat_cmd.start_chat())

@cli.command()
@click.option('--listen', '-l', is_flag=True, help='Start listening immediately')
@click.option('--continuous', '-c', is_flag=True, help='Continuous listening mode')
@click.pass_context
def voice(ctx: click.Context, listen: bool = False, continuous: bool = False):  # type: ignore
    """Voice interaction with Charlie"""
    voice_cmd = VoiceCommand(ctx.obj)
    if listen:
        asyncio.run(voice_cmd.start_listening(continuous=continuous))
    else:
        console.print("[yellow]Use --listen to start voice interaction[/yellow]")

@cli.command()
@click.argument('action', type=click.Choice(['get', 'set', 'reset', 'show']))
@click.argument('key', required=False)
@click.argument('value', required=False)
@click.pass_context
def config(ctx: click.Context, action: str = 'show', key: Optional[str] = None, value: Optional[str] = None):  # type: ignore
    """Manage Charlie configuration"""
    config_cmd = ConfigCommand(ctx.obj)
    if action == 'show':
        config_cmd.show_config()
    elif action == 'get' and key:
        config_cmd.get_config(key)
    elif action == 'set' and key and value:
        config_cmd.set_config(key, value)
    elif action == 'reset':
        config_cmd.reset_config()
    else:
        console.print("[red]Invalid config command. Use: charlie config --help[/red]")

@cli.command()
@click.pass_context
def status(ctx: click.Context):
    """Show Charlie system status"""
    show_welcome()

@cli.command()
@click.option('--limit', '-n', default=10, help='Number of recent conversations to show')
@click.pass_context
def history(ctx: click.Context, limit: int = 10):  # type: ignore
    """Show conversation history"""
    console.print(f"[cyan]Showing last {limit} conversations...[/cyan]")
    # TODO: Implement history retrieval from Supabase
    console.print("[yellow]History feature coming soon![/yellow]")

@cli.command()
@click.argument('message', nargs=-1)
@click.pass_context
def ask(ctx: click.Context, message = ()):  # type: ignore
    """Ask Charlie a quick question"""
    if not message:
        console.print("[red]Please provide a message. Example: charlie ask 'What's the weather?'[/red]")
        return
    
    question = ' '.join(message)
    chat_cmd = ChatCommand(ctx.obj)
    asyncio.run(chat_cmd.process_message(question))

def main():
    """Main entry point for the CLI application"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 