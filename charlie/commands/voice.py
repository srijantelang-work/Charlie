"""
Voice command for Charlie CLI - Voice interaction interface
"""

import asyncio
import pyaudio
import wave
import tempfile
import os
import threading
import time
from typing import Optional, Callable

try:
    from rich.console import Console  # type: ignore
    from rich.live import Live  # type: ignore
    from rich.panel import Panel  # type: ignore
    from rich.text import Text  # type: ignore
    import keyboard  # type: ignore
    RICH_AVAILABLE = True
    KEYBOARD_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    KEYBOARD_AVAILABLE = False
    # Fallback if dependencies not installed
    class Console:
        def print(self, *args, **kwargs): print(*args)
    
    class Live:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def update(self, *args, **kwargs): pass
        def stop(self): pass
    
    class Panel:
        def __init__(self, *args, **kwargs): pass
    
    class Text:
        def __init__(self, *args, **kwargs): pass
        def append(self, *args, **kwargs): pass
    
    # Mock keyboard module
    class KeyboardModule:
        @staticmethod
        def add_hotkey(*args, **kwargs): pass
        @staticmethod
        def unhook_all(): pass
    
    keyboard = KeyboardModule()

from charlie.utils.voice import VoiceProcessor
from charlie.commands.chat import ChatCommand
from charlie.ui.components import (
    create_voice_indicator,
    create_thinking_indicator,
    create_error_panel,
    create_success_panel
)

class VoiceCommand:
    """Handles voice interactions with Charlie"""
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.console = Console()
        self.voice_processor = VoiceProcessor(ctx)
        self.chat_command = ChatCommand(ctx)
        self.is_listening = False
        self.continuous_mode = False
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.audio_format = pyaudio.paInt16
        
        # Wake word detection
        self.wake_word = ctx.config.get('wake_word')
        self.voice_threshold = ctx.config.get('voice_threshold')
    
    async def start_listening(self, continuous: bool = False):
        """Start voice interaction session"""
        
        self.continuous_mode = continuous
        
        if continuous:
            await self.start_continuous_listening()
        else:
            await self.start_single_interaction()
    
    async def start_single_interaction(self):
        """Single voice interaction"""
        
        self.console.print(Panel(
            "🎤 Voice interaction mode\nPress SPACE to start recording, release to stop\nPress ESC to exit",
            title="[bold green]Voice Mode[/bold green]", 
            border_style="green"
        ))
        
        try:
            # Set up keyboard listeners
            keyboard.add_hotkey('space', self.start_recording)
            keyboard.add_hotkey('esc', self.stop_voice_mode)
            
            # Show voice indicator
            with Live(create_voice_indicator(False), refresh_per_second=2) as live:
                while not self.should_exit:
                    if self.is_listening:
                        live.update(create_voice_indicator(True))
                    else:
                        live.update(create_voice_indicator(False))
                    
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            self.console.print(create_error_panel(f"Voice mode error: {str(e)}"))
        
        finally:
            keyboard.unhook_all()
    
    async def start_continuous_listening(self):
        """Continuous listening with wake word detection"""
        
        self.console.print(Panel(
            f"🎤 Continuous listening mode active\nSay '{self.wake_word}' to activate\nPress CTRL+C to exit",
            title="[bold green]Always Listening[/bold green]",
            border_style="green"
        ))
        
        try:
            while True:
                # Listen for wake word
                if await self.detect_wake_word():
                    self.console.print(create_success_panel("Wake word detected! Listening..."))
                    
                    # Record and process voice
                    await self.process_voice_input()
                
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Continuous listening stopped[/yellow]")
    
    async def detect_wake_word(self) -> bool:
        """Detect wake word in audio stream"""
        
        try:
            # Record short audio sample
            audio_data = await self.record_audio_chunk(duration=2)
            
            # Process with STT to check for wake word
            text = await self.voice_processor.speech_to_text(audio_data)
            
            if text and self.wake_word.lower() in text.lower():
                return True
                
        except Exception as e:
            if self.ctx.debug:
                self.console.print(f"[dim]Wake word detection error: {e}[/dim]")
        
        return False
    
    async def process_voice_input(self):
        """Process voice input and generate response"""
        
        try:
            # Show listening indicator
            with Live(create_voice_indicator(True), refresh_per_second=4) as live:
                # Record audio
                audio_data = await self.record_audio_command()
                
                live.update(create_thinking_indicator())
                
                # Convert speech to text
                text = await self.voice_processor.speech_to_text(audio_data)
                
                if text:
                    self.console.print(Panel(
                        f"You said: {text}",
                        title="[bold blue]Voice Input[/bold blue]",
                        border_style="blue"
                    ))
                    
                    # Process with chat command
                    response = await self.chat_command.process_message(text)
                    
                    if response:
                        # Convert response to speech
                        await self.voice_processor.text_to_speech(response)
                        
                else:
                    live.stop()
                    self.console.print(create_error_panel("Could not understand voice input"))
                    
        except Exception as e:
            self.console.print(create_error_panel(f"Voice processing error: {str(e)}"))
    
    async def record_audio_chunk(self, duration: float = 2.0) -> bytes:
        """Record a short audio chunk"""
        
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            num_chunks = int(self.sample_rate / self.chunk_size * duration)
            
            for _ in range(num_chunks):
                data = stream.read(self.chunk_size)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            return b''.join(frames)
            
        finally:
            audio.terminate()
    
    async def record_audio_command(self, max_duration: float = 10.0) -> bytes:
        """Record audio for voice command with silence detection"""
        
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=self.audio_format,
                channels=self.channels, 
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            silence_chunks = 0
            max_silence_chunks = int(self.sample_rate / self.chunk_size * 2)  # 2 seconds of silence
            max_chunks = int(self.sample_rate / self.chunk_size * max_duration)
            
            for i in range(max_chunks):
                data = stream.read(self.chunk_size)
                frames.append(data)
                
                # Simple silence detection (you might want to improve this)
                volume = self.get_audio_level(data)
                if volume < self.voice_threshold:
                    silence_chunks += 1
                else:
                    silence_chunks = 0
                
                # Stop if we've had enough silence
                if silence_chunks >= max_silence_chunks and len(frames) > 8:  # At least 0.5 seconds recorded
                    break
            
            stream.stop_stream()
            stream.close()
            
            return b''.join(frames)
            
        finally:
            audio.terminate()
    
    def get_audio_level(self, data: bytes) -> float:
        """Get audio level for silence detection"""
        
        import struct
        
        # Convert bytes to integers and calculate RMS
        fmt = f"{len(data)//2}h"
        samples = struct.unpack(fmt, data)
        rms = (sum(sample**2 for sample in samples) / len(samples)) ** 0.5
        
        return rms / 32768.0  # Normalize to 0-1 range
    
    def start_recording(self):
        """Start recording callback"""
        self.is_listening = True
    
    def stop_recording(self):
        """Stop recording callback"""
        self.is_listening = False
    
    def stop_voice_mode(self):
        """Exit voice mode callback"""
        self.should_exit = True
    
    async def test_voice_system(self):
        """Test voice system components"""
        
        self.console.print(Panel(
            "Testing voice system components...",
            title="[bold yellow]Voice System Test[/bold yellow]",
            border_style="yellow"
        ))
        
        try:
            # Test microphone
            self.console.print("🎤 Testing microphone...")
            audio_data = await self.record_audio_chunk(duration=1.0)
            level = self.get_audio_level(audio_data)
            
            if level > 0.01:
                self.console.print(create_success_panel("Microphone working"))
            else:
                self.console.print(create_error_panel("Microphone not detecting sound"))
            
            # Test STT
            self.console.print("🗣️  Testing speech-to-text...")
            test_result = await self.voice_processor.test_stt()
            
            if test_result:
                self.console.print(create_success_panel("Speech-to-text ready"))
            else:
                self.console.print(create_error_panel("Speech-to-text not working"))
            
            # Test TTS
            self.console.print("🔊 Testing text-to-speech...")
            await self.voice_processor.text_to_speech("Voice system test complete")
            self.console.print(create_success_panel("Text-to-speech ready"))
            
        except Exception as e:
            self.console.print(create_error_panel(f"Voice system test failed: {str(e)}"))
    
    def __del__(self):
        """Cleanup"""
        try:
            keyboard.unhook_all()
        except:
            pass 