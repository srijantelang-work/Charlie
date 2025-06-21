"""
Layout components for Charlie CLI
"""

try:
    from rich.console import Console, Group
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.columns import Columns
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback if Rich is not installed yet
    class Console:
        def print(self, *args, **kwargs): print(*args)
    class Group:
        def __init__(self, *args, **kwargs): pass
    class Layout:
        def __init__(self, *args, **kwargs): pass
        def split_column(self, *args, **kwargs): pass
        def split_row(self, *args, **kwargs): pass
        def __getitem__(self, key): return self
    class Panel:
        def __init__(self, *args, **kwargs): pass
    class Text:
        def __init__(self, *args, **kwargs): pass
        def append(self, *args, **kwargs): pass
    class Table:
        @staticmethod
        def grid(*args, **kwargs): return Table()
        def __init__(self, *args, **kwargs): pass
        def add_column(self, *args, **kwargs): pass
        def add_row(self, *args, **kwargs): pass
    class Columns:
        def __init__(self, *args, **kwargs): pass
    class Align:
        @staticmethod
        def center(*args, **kwargs): pass

def create_main_layout():
    """Create main CLI layout"""
    
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    layout["main"].split_row(
        Layout(name="chat", ratio=3),
        Layout(name="sidebar", ratio=1)
    )
    
    return layout

def create_header_layout(title: str = "Charlie CLI"):
    """Create header layout"""
    
    header_text = Text()
    header_text.append("🤖 ", style="blue")
    header_text.append(title, style="bold cyan")
    header_text.append(" | Voice-Controlled AI Assistant", style="dim")
    
    return Panel(
        Align.center(header_text),
        style="blue"
    )

def create_footer_layout(status: str = "Ready"):
    """Create footer layout"""
    
    footer_table = Table.grid(padding=1)
    footer_table.add_column(justify="left")
    footer_table.add_column(justify="center") 
    footer_table.add_column(justify="right")
    
    footer_table.add_row(
        f"Status: {status}",
        "Press Ctrl+C to exit",
        "Type 'help' for commands"
    )
    
    return Panel(
        footer_table,
        style="green"
    )

def create_sidebar_layout(config_info: dict):
    """Create sidebar layout with system info"""
    
    info_table = Table(show_header=False, box=None)
    info_table.add_column("", style="cyan")
    info_table.add_column("", style="white")
    
    info_table.add_row("🔑 API", "Connected" if config_info.get('has_api_key') else "Missing")
    info_table.add_row("🎤 Voice", "Ready" if config_info.get('voice_ready') else "Disabled")
    info_table.add_row("💾 Memory", "Active" if config_info.get('memory_active') else "Inactive")
    info_table.add_row("🌐 Backend", "Online" if config_info.get('backend_online') else "Offline")
    
    return Panel(
        info_table,
        title="[bold]System Status[/bold]",
        border_style="yellow"
    )

def create_chat_layout():
    """Create chat area layout"""
    
    return Panel(
        Text("Chat messages will appear here...", style="dim"),
        title="[bold green]Conversation[/bold green]",
        border_style="green"
    )

def create_split_view(left_content, right_content, left_title="Main", right_title="Info"):
    """Create split view layout"""
    
    left_panel = Panel(left_content, title=f"[bold]{left_title}[/bold]")
    right_panel = Panel(right_content, title=f"[bold]{right_title}[/bold]")
    
    return Columns([left_panel, right_panel], equal=False, expand=True) 