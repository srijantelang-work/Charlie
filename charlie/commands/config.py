"""
Configuration command for Charlie CLI - Manage settings and preferences
"""

from typing import Optional

try:
    from rich.console import Console  # type: ignore
    from rich.panel import Panel  # type: ignore
    from rich.table import Table  # type: ignore
    from rich.prompt import Prompt, Confirm  # type: ignore
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback if Rich is not installed yet
    class Console:
        def print(self, *args, **kwargs): print(*args)
    
    class Panel:
        def __init__(self, *args, **kwargs): pass
        
    class Table:
        def __init__(self, *args, **kwargs): pass
        def add_column(self, *args, **kwargs): pass
        def add_row(self, *args, **kwargs): pass
    
    class Prompt:
        @staticmethod
        def ask(*args, **kwargs): return input(*args)
    
    class Confirm:
        @staticmethod
        def ask(*args, **kwargs): return input(*args).lower() in ['y', 'yes', 'true', '1']

from charlie.ui.components import (
    create_config_table,
    create_success_panel,
    create_error_panel
)

class ConfigCommand:
    """Handles configuration management for Charlie CLI"""
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.console = Console()
    
    def show_config(self):
        """Display current configuration"""
        
        config_data = self.ctx.config.get_all()
        table = create_config_table(config_data)
        
        self.console.print(Panel(
            table,
            title="[bold cyan]Charlie Configuration[/bold cyan]",
            border_style="cyan"
        ))
        
        self.console.print("\n[dim]Use 'charlie config set <key> <value>' to change settings[/dim]")
    
    def get_config(self, key: str):
        """Get a specific configuration value"""
        
        value = self.ctx.config.get(key)
        
        if value is not None:
            # Hide sensitive keys
            if key.endswith('_key') or key.endswith('_secret'):
                display_value = '***hidden***'
            else:
                display_value = str(value)
            
            self.console.print(f"[cyan]{key}[/cyan]: [green]{display_value}[/green]")
        else:
            self.console.print(f"[red]Configuration key '{key}' not found[/red]")
    
    def set_config(self, key: str, value: str):
        """Set a configuration value"""
        
        # Special handling for sensitive keys
        if key.endswith('_key') or key.endswith('_secret'):
            if not value or value == '':
                value = Prompt.ask(f"Enter {key}", password=True)
        
        if self.ctx.config.set(key, value):
            self.console.print(create_success_panel(f"Set {key} = {value if not key.endswith('_key') else '***hidden***'}"))
            
            # Provide helpful next steps
            if key == 'gemini_api_key':
                self.console.print("[dim]You can now use Charlie's AI features![/dim]")
            elif key == 'backend_url':
                self.console.print("[dim]Use 'charlie status' to test the connection[/dim]")
        else:
            self.console.print(create_error_panel(f"Failed to set {key}"))
    
    def reset_config(self):
        """Reset configuration to defaults"""
        
        if Confirm.ask("[red]Are you sure you want to reset all configuration to defaults?[/red]"):
            self.ctx.config.reset()
            self.console.print(create_success_panel("Configuration reset to defaults"))
        else:
            self.console.print("[yellow]Configuration reset cancelled[/yellow]")
    
    def setup_wizard(self):
        """Interactive setup wizard for first-time users"""
        
        self.console.print(Panel(
            "Welcome to Charlie! Let's set up your configuration.",
            title="[bold blue]Setup Wizard[/bold blue]",
            border_style="blue"
        ))
        
        # Check if already configured
        if self.ctx.config.get('gemini_api_key'):
            if not Confirm.ask("Configuration already exists. Do you want to reconfigure?"):
                self.console.print("[yellow]Setup cancelled[/yellow]")
                return
        
        try:
            # Get API keys
            self.console.print("\n[bold]Step 1: API Configuration[/bold]")
            self.console.print("You'll need API keys from Google Cloud and Supabase.")
            
            gemini_key = Prompt.ask("Google Gemini API Key", password=True)
            if gemini_key:
                self.ctx.config.set('gemini_api_key', gemini_key)
            
            supabase_url = Prompt.ask("Supabase Project URL (optional)", default="")
            if supabase_url:
                self.ctx.config.set('supabase_url', supabase_url)
                
                supabase_key = Prompt.ask("Supabase API Key", password=True)
                if supabase_key:
                    self.ctx.config.set('supabase_key', supabase_key)
            
            # Voice settings
            self.console.print("\n[bold]Step 2: Voice Configuration[/bold]")
            
            wake_word = Prompt.ask("Wake word for voice activation", default="Hey Charlie")
            self.ctx.config.set('wake_word', wake_word)
            
            language = Prompt.ask("Preferred language for voice", default="en-US")
            self.ctx.config.set('stt_language', language)
            
            # Backend settings
            self.console.print("\n[bold]Step 3: Backend Configuration[/bold]")
            
            backend_url = Prompt.ask("Backend API URL", default="http://localhost:8000")
            self.ctx.config.set('backend_url', backend_url)
            
            # CLI preferences
            self.console.print("\n[bold]Step 4: CLI Preferences[/bold]")
            
            auto_save = Confirm.ask("Auto-save conversation history?", default=True)
            self.ctx.config.set('auto_save_history', auto_save)
            
            show_timestamps = Confirm.ask("Show timestamps in conversations?", default=True)
            self.ctx.config.set('show_timestamps', show_timestamps)
            
            self.console.print(create_success_panel("Setup complete! Charlie is ready to use."))
            self.console.print("\n[dim]You can change these settings anytime with 'charlie config set <key> <value>'[/dim]")
            self.console.print("[dim]Try 'charlie chat' to start a conversation or 'charlie voice --listen' for voice interaction[/dim]")
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Setup interrupted[/yellow]")
        except Exception as e:
            self.console.print(create_error_panel(f"Setup failed: {str(e)}"))
    
    def validate_config(self):
        """Validate current configuration"""
        
        self.console.print("🔍 Validating configuration...")
        
        issues = []
        warnings = []
        
        # Check required API keys
        if not self.ctx.config.get('gemini_api_key'):
            issues.append("Missing Gemini API key - AI features won't work")
        
        # Check URLs
        backend_url = self.ctx.config.get('backend_url')
        if not backend_url or not backend_url.startswith('http'):
            issues.append("Invalid backend URL")
        
        # Check voice settings
        language = self.ctx.config.get('stt_language')
        if language and not language.replace('-', '').replace('_', '').isalnum():
            warnings.append("Invalid language code format")
        
        # Check numeric values
        threshold = self.ctx.config.get('voice_threshold')
        if threshold and (threshold < 0 or threshold > 1):
            warnings.append("Voice threshold should be between 0 and 1")
        
        # Display results
        if not issues and not warnings:
            self.console.print(create_success_panel("Configuration is valid!"))
        else:
            if issues:
                self.console.print(Panel(
                    "\n".join(f"❌ {issue}" for issue in issues),
                    title="[bold red]Issues Found[/bold red]",
                    border_style="red"
                ))
            
            if warnings:
                self.console.print(Panel(
                    "\n".join(f"⚠️  {warning}" for warning in warnings),
                    title="[bold yellow]Warnings[/bold yellow]",
                    border_style="yellow"
                ))
            
            self.console.print("\n[dim]Use 'charlie config set <key> <value>' to fix issues[/dim]")
    
    def export_config(self, file_path: Optional[str] = None):
        """Export configuration to file"""
        
        if not file_path:
            file_path = f"charlie-config-{self.ctx.config.get('theme')}.yaml"
        
        try:
            import shutil
            shutil.copy(self.ctx.config.config_file, file_path)
            self.console.print(create_success_panel(f"Configuration exported to {file_path}"))
        except Exception as e:
            self.console.print(create_error_panel(f"Export failed: {str(e)}"))
    
    def import_config(self, file_path: str):
        """Import configuration from file"""
        
        try:
            from pathlib import Path
            
            if not Path(file_path).exists():
                self.console.print(create_error_panel(f"File not found: {file_path}"))
                return
            
            if Confirm.ask(f"This will overwrite your current configuration. Continue?"):
                self.ctx.config.load_config(Path(file_path))
                self.console.print(create_success_panel(f"Configuration imported from {file_path}"))
                
                # Validate imported config
                self.validate_config()
            else:
                self.console.print("[yellow]Import cancelled[/yellow]")
                
        except Exception as e:
            self.console.print(create_error_panel(f"Import failed: {str(e)}"))
    
    def list_themes(self):
        """List available CLI themes"""
        
        themes = ['dark', 'light', 'auto']
        current_theme = self.ctx.config.get('theme')
        
        self.console.print("[bold]Available themes:[/bold]")
        for theme in themes:
            marker = "✓" if theme == current_theme else " "
            self.console.print(f"{marker} {theme}")
        
        self.console.print(f"\n[dim]Use 'charlie config set theme <theme>' to change[/dim]") 