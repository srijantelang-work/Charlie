"""
Configuration management for Charlie CLI
"""

import os
import yaml
try:
    import toml  # type: ignore
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False
    # Fallback if toml is not installed
    # Create a simple object to mock the toml module
    class TomlMock:
        def __init__(self):
            pass
        
        def load(self, f):  # type: ignore
            return {}
    
    toml = TomlMock()

from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    from rich.console import Console  # type: ignore
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback if Rich is not installed
    class Console:
        def print(self, *args, **kwargs): print(*args)

console = Console()

@dataclass
class ConfigSchema:
    """Configuration schema for Charlie CLI"""
    
    # API Keys
    gemini_api_key: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    # Voice Settings
    stt_language: str = "en-US"
    tts_voice: str = "en-US-Neural2-F"
    wake_word: str = "Hey Charlie"
    voice_threshold: float = 0.5
    
    # API Settings
    backend_url: str = "http://localhost:8000"
    timeout: int = 30
    
    # CLI Settings
    auto_save_history: bool = True
    max_history_entries: int = 100
    theme: str = "dark"
    show_timestamps: bool = True
    
    # Advanced Settings
    debug_mode: bool = False
    verbose_logging: bool = False

class ConfigManager:
    """Manages Charlie CLI configuration"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.charlie'
        self.config_file = self.config_dir / 'config.yaml'
        self.config_dir.mkdir(exist_ok=True)
        
        self.config = ConfigSchema()
        self.load_config()
    
    def load_config(self, config_path: Optional[Path] = None) -> None:
        """Load configuration from file"""
        
        config_file = config_path or self.config_file
        
        if not config_file.exists():
            self.create_default_config()
            return
        
        try:
            if config_file.suffix == '.yaml' or config_file.suffix == '.yml':
                with open(config_file, 'r') as f:
                    data = yaml.safe_load(f) or {}
            elif config_file.suffix == '.toml':
                with open(config_file, 'r') as f:
                    data = toml.load(f)
            else:
                console.print(f"[red]Unsupported config file format: {config_file.suffix}[/red]")
                return
            
            # Update config with loaded data
            for key, value in data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    
        except Exception as e:
            console.print(f"[red]Error loading config: {e}[/red]")
            self.create_default_config()
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        
        try:
            config_data = {
                'gemini_api_key': self.config.gemini_api_key,
                'supabase_url': self.config.supabase_url,
                'supabase_key': self.config.supabase_key,
                'stt_language': self.config.stt_language,
                'tts_voice': self.config.tts_voice,
                'wake_word': self.config.wake_word,
                'voice_threshold': self.config.voice_threshold,
                'backend_url': self.config.backend_url,
                'timeout': self.config.timeout,
                'auto_save_history': self.config.auto_save_history,
                'max_history_entries': self.config.max_history_entries,
                'theme': self.config.theme,
                'show_timestamps': self.config.show_timestamps,
                'debug_mode': self.config.debug_mode,
                'verbose_logging': self.config.verbose_logging
            }
            
            with open(self.config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
                
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")
    
    def create_default_config(self) -> None:
        """Create default configuration file"""
        
        self.config = ConfigSchema()
        
        # Try to get API keys from environment
        self.config.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.config.supabase_url = os.getenv('SUPABASE_URL')
        self.config.supabase_key = os.getenv('SUPABASE_KEY')
        
        self.save_config()
        
        console.print(f"[green]Created default config at: {self.config_file}[/green]")
        if not self.config.gemini_api_key:
            console.print("[yellow]Please set your API keys using 'charlie config set'[/yellow]")
    
    def get(self, key: str) -> Any:
        """Get configuration value"""
        return getattr(self.config, key, None)
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        
        if not hasattr(self.config, key):
            console.print(f"[red]Unknown config key: {key}[/red]")
            return False
        
        # Type conversion based on current value
        current_value = getattr(self.config, key)
        if current_value is not None:
            if isinstance(current_value, bool):
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(current_value, int):
                value = int(value)
            elif isinstance(current_value, float):
                value = float(value)
        
        setattr(self.config, key, value)
        self.save_config()
        return True
    
    def reset(self) -> None:
        """Reset configuration to defaults"""
        
        if self.config_file.exists():
            self.config_file.unlink()
        
        self.create_default_config()
        console.print("[green]Configuration reset to defaults[/green]")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        
        return {
            'gemini_api_key': {'value': self.config.gemini_api_key, 'description': 'Google Gemini API key'},
            'supabase_url': {'value': self.config.supabase_url, 'description': 'Supabase project URL'},
            'supabase_key': {'value': self.config.supabase_key, 'description': 'Supabase API key'},
            'stt_language': {'value': self.config.stt_language, 'description': 'Speech-to-text language'},
            'tts_voice': {'value': self.config.tts_voice, 'description': 'Text-to-speech voice'},
            'wake_word': {'value': self.config.wake_word, 'description': 'Voice activation phrase'},
            'voice_threshold': {'value': self.config.voice_threshold, 'description': 'Voice detection threshold'},
            'backend_url': {'value': self.config.backend_url, 'description': 'Backend API URL'},
            'timeout': {'value': self.config.timeout, 'description': 'API timeout in seconds'},
            'auto_save_history': {'value': self.config.auto_save_history, 'description': 'Save conversation history'},
            'max_history_entries': {'value': self.config.max_history_entries, 'description': 'Max history entries'},
            'theme': {'value': self.config.theme, 'description': 'CLI theme (dark/light)'},
            'show_timestamps': {'value': self.config.show_timestamps, 'description': 'Show timestamps in chat'},
            'debug_mode': {'value': self.config.debug_mode, 'description': 'Enable debug logging'},
            'verbose_logging': {'value': self.config.verbose_logging, 'description': 'Verbose log output'}
        } 