"""
Rich UI components for Charlie CLI interface
"""

try:
    from rich.panel import Panel # type: ignore
    from rich.text import Text # type: ignore
    from rich.table import Table # type: ignore
    from rich.console import Group # type: ignore
    from rich.align import Align # type: ignore
    from rich.columns import Columns # type: ignore
    from rich import box # type: ignore
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback implementations
    class Panel:
        def __init__(self, *args, **kwargs): pass
    class Text:
        def __init__(self, *args, **kwargs): pass
        def append(self, *args, **kwargs): pass
    class Table:
        def __init__(self, *args, **kwargs): pass
        def add_column(self, *args, **kwargs): pass
        def add_row(self, *args, **kwargs): pass
    class Group:
        def __init__(self, *args, **kwargs): pass
    class Align:
        @staticmethod
        def center(*args, **kwargs): pass
    class Columns:
        def __init__(self, *args, **kwargs): pass
    class box:
        ROUNDED = None

def create_welcome_panel() -> Panel:
    """Create the main welcome panel for Charlie CLI"""
    
    # Create the ASCII art for Charlie
    ascii_art = """
    ╭─────────────────────────────────────╮
    │           ⚡ CHARLIE ⚡              │
    │    Voice-Controlled AI Assistant    │
    │         Powered by Gemini 2.5       │
    ╰─────────────────────────────────────╯
    """
    
    welcome_text = Text()
    welcome_text.append(ascii_art, style="bold cyan")
    welcome_text.append("\n")
    welcome_text.append("🎤 Say 'Hey Charlie' to activate voice mode\n", style="green")
    welcome_text.append("💬 Type your questions or commands\n", style="blue")
    welcome_text.append("⚙️  Use 'charlie --help' for all commands\n", style="yellow")
    
    return Panel(
        Align.center(welcome_text),
        title="[bold blue]Welcome to Charlie[/bold blue]",
        border_style="blue",
        box=box.ROUNDED
    )

def create_status_panel(status_data: dict) -> Panel:
    """Create system status panel"""
    
    status_table = Table(show_header=False, box=None, padding=(0, 2))
    status_table.add_column("Component", style="cyan", no_wrap=True)
    status_table.add_column("Status", style="green")
    
    for component, status in status_data.items():
        status_table.add_row(f"🔧 {component}", status)
    
    return Panel(
        status_table,
        title="[bold green]System Status[/bold green]",
        border_style="green"
    )

def create_chat_bubble(message: str, is_user: bool = True) -> Panel:
    """Create chat bubble for conversations"""
    
    if is_user:
        return Panel(
            message,
            title="[bold blue]You[/bold blue]",
            border_style="blue",
            box=box.ROUNDED
        )
    else:
        return Panel(
            message,
            title="[bold green]Charlie[/bold green]", 
            border_style="green",
            box=box.ROUNDED
        )

def create_voice_indicator(is_listening: bool = False) -> Text:
    """Create voice status indicator"""
    
    if is_listening:
        indicator = Text()
        indicator.append("🎤", style="bold red blink")
        indicator.append(" LISTENING...", style="bold red")
        return indicator
    else:
        indicator = Text()
        indicator.append("🎤", style="dim")
        indicator.append(" Press SPACE to talk", style="dim")
        return indicator

def create_thinking_indicator() -> Text:
    """Create thinking indicator for AI processing"""
    
    indicator = Text()
    indicator.append("🤔", style="bold yellow")
    indicator.append(" Charlie is thinking...", style="bold yellow")
    return indicator

def create_error_panel(error_message: str) -> Panel:
    """Create error message panel"""
    
    return Panel(
        f"❌ {error_message}",
        title="[bold red]Error[/bold red]",
        border_style="red"
    )

def create_success_panel(success_message: str) -> Panel:
    """Create success message panel"""
    
    return Panel(
        f"✅ {success_message}",
        title="[bold green]Success[/bold green]",
        border_style="green"
    )

def create_command_history_table(history: list) -> Table:
    """Create command history table"""
    
    table = Table(title="Command History")
    table.add_column("Time", style="cyan", no_wrap=True)
    table.add_column("Command", style="white")
    table.add_column("Response", style="green")
    
    for entry in history[-10:]:  # Show last 10 entries
        table.add_row(
            entry.get('timestamp', ''),
            entry.get('command', ''),
            entry.get('response', '')[:50] + '...' if len(entry.get('response', '')) > 50 else entry.get('response', '')
        )
    
    return table

def create_config_table(config_data: dict) -> Table:
    """Create configuration table"""
    
    table = Table(title="Charlie Configuration")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_column("Description", style="dim")
    
    for key, value in config_data.items():
        if isinstance(value, dict) and 'value' in value:
            table.add_row(
                key,
                str(value['value']) if not key.endswith('_key') else '***hidden***',
                value.get('description', '')
            )
        else:
            table.add_row(key, str(value), '')
    
    return table 