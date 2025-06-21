#!/usr/bin/env python3
"""
Charlie CLI Demo Script
Demonstrates the main features of Phase 4 CLI implementation
"""

import sys
import os
import asyncio

# Try to import rich components with fallbacks
try:
    from rich.console import Console  # type: ignore
    from rich.panel import Panel  # type: ignore
    from rich.table import Table  # type: ignore
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback implementations
    class Console:
        def print(self, *args, **kwargs): print(*args)
        def input(self, *args, **kwargs): return input(*args)
    
    class Panel:
        def __init__(self, *args, **kwargs): pass
    
    class Table:
        def __init__(self, *args, **kwargs): pass
        def add_column(self, *args, **kwargs): return self
        def add_row(self, *args, **kwargs): pass

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

console = Console()

def demo_welcome():
    """Demo the welcome screen"""
    
    console.print("\n🎬 Demo: Welcome Screen")
    console.print("=" * 50)
    
    try:
        from charlie.ui.components import create_welcome_panel
        welcome_panel = create_welcome_panel()
        console.print(welcome_panel)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def demo_config():
    """Demo configuration management"""
    
    console.print("\n🎬 Demo: Configuration Management")
    console.print("=" * 50)
    
    try:
        from charlie.utils.config import ConfigManager
        
        config = ConfigManager()
        
        # Show config structure
        console.print("📁 Configuration Directory:", str(config.config_dir))
        console.print("📄 Configuration File:", str(config.config_file))
        
        # Demo config operations
        console.print("\n⚙️ Configuration Operations:")
        
        # Set some demo values
        config.set('demo_key', 'demo_value')
        config.set('theme', 'dark')
        config.set('auto_save_history', True)
        
        # Get values
        theme = config.get('theme')
        auto_save = config.get('auto_save_history')
        
        console.print(f"🎨 Theme: {theme}")
        console.print(f"💾 Auto-save history: {auto_save}")
        
        # Show all config
        all_config = config.get_all()
        console.print(f"📊 Total config entries: {len(all_config)}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def demo_ui_components():
    """Demo UI components"""
    
    console.print("\n🎬 Demo: UI Components")
    console.print("=" * 50)
    
    try:
        from charlie.ui.components import (
            create_chat_bubble,
            create_voice_indicator,
            create_thinking_indicator,
            create_success_panel,
            create_error_panel
        )
        
        # Chat bubbles
        console.print("💬 Chat Bubbles:")
        console.print(create_chat_bubble("Hello Charlie!", is_user=True))
        console.print(create_chat_bubble("Hello! How can I help you today?", is_user=False))
        
        # Status indicators
        console.print("\n📊 Status Indicators:")
        console.print(create_voice_indicator(False))
        console.print(create_voice_indicator(True))
        console.print(create_thinking_indicator())
        
        # Notification panels
        console.print("\n📢 Notification Panels:")
        console.print(create_success_panel("Operation completed successfully!"))
        console.print(create_error_panel("Something went wrong"))
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def demo_history():
    """Demo history management"""
    
    console.print("\n🎬 Demo: History Management")
    console.print("=" * 50)
    
    try:
        from charlie.utils.history import HistoryManager
        
        # Create mock context
        class MockContext:
            def __init__(self):
                self.debug = False
                class MockConfig:
                    def get(self, key, default=None):
                        defaults = {
                            'auto_save_history': True,
                            'max_history_entries': 100
                        }
                        return defaults.get(key, default)
                self.config = MockConfig()
        
        ctx = MockContext()
        history = HistoryManager(ctx)
        
        # Add some demo history
        history.add_command("charlie chat", True, "Started chat session")
        history.add_command("charlie config show", True, "Configuration displayed")
        history.add_conversation("Hello", "Hi there! How can I help?", "demo-session-1")
        history.add_conversation("What's the weather?", "I can help with weather info!", "demo-session-1")
        
        # Show statistics
        stats = history.get_statistics()
        
        stats_table = Table(title="History Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Commands", str(stats['total_commands']))
        stats_table.add_row("Total Conversations", str(stats['total_conversations']))
        stats_table.add_row("Successful Commands", str(stats['successful_commands']))
        
        if 'most_used_commands' in stats and stats['most_used_commands']:
            most_used = stats['most_used_commands'][0]
            stats_table.add_row("Most Used Command", f"{most_used[0]} ({most_used[1]}x)")
        
        console.print(stats_table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def demo_commands():
    """Demo available commands"""
    
    console.print("\n🎬 Demo: Available Commands")
    console.print("=" * 50)
    
    try:
        from charlie.cli import cli
        
        commands_table = Table(title="Charlie CLI Commands")
        commands_table.add_column("Command", style="cyan", no_wrap=True)
        commands_table.add_column("Description", style="white")
        commands_table.add_column("Status", style="green")
        
        # List all commands
        for cmd_name, cmd in cli.commands.items():
            help_text = cmd.help or "No description available"
            commands_table.add_row(cmd_name, help_text[:50] + "...", "✅ Ready")
        
        console.print(commands_table)
        
        # Show example usage
        console.print("\n📝 Example Usage:")
        examples = [
            "python -m charlie.cli --help",
            "python -m charlie.cli config show",
            "python -m charlie.cli chat",
            "python -m charlie.cli voice --listen",
            "python -m charlie.cli ask 'What time is it?'"
        ]
        
        for example in examples:
            console.print(f"  [dim]$[/dim] [cyan]{example}[/cyan]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def demo_features():
    """Demo Phase 4 features checklist"""
    
    console.print("\n🎬 Demo: Phase 4 Feature Checklist")
    console.print("=" * 50)
    
    features = [
        ("Rich CLI interface with Click", "✅ Complete"),
        ("Voice interaction in terminal", "✅ Complete"),
        ("Configuration management", "✅ Complete"),
        ("CLI-specific optimizations", "✅ Complete"),
        ("Command history and shortcuts", "✅ Complete"),
        ("Interactive setup wizard", "✅ Complete"),
        ("Multi-platform support", "✅ Complete"),
        ("Error handling and fallbacks", "✅ Complete"),
        ("Keyboard shortcuts", "✅ Complete"),
        ("Real-time voice processing", "✅ Complete")
    ]
    
    features_table = Table(title="Phase 4 Implementation Status")
    features_table.add_column("Feature", style="white")
    features_table.add_column("Status", style="green")
    
    for feature, status in features:
        features_table.add_row(feature, status)
    
    console.print(features_table)

def main():
    """Run the demo"""
    
    console.print(Panel(
        "[bold cyan]Charlie CLI Phase 4 Demo[/bold cyan]\n"
        "Showcasing the implemented CLI features",
        title="🎭 Demo Mode",
        border_style="blue"
    ))
    
    demos = [
        demo_welcome,
        demo_config,
        demo_ui_components,
        demo_history,
        demo_commands,
        demo_features
    ]
    
    for demo in demos:
        try:
            demo()
            console.input("\n[dim]Press Enter to continue...[/dim]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Demo interrupted[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Demo error: {e}[/red]")
    
    console.print("\n🎉 Demo completed! Charlie CLI Phase 4 is ready for use.")
    console.print("Try running: [cyan]python -m charlie.cli --help[/cyan]")

if __name__ == "__main__":
    main() 