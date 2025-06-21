"""
Chat command for Charlie CLI - Text-based conversation interface
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
try:
    from rich.console import Console # type: ignore
    from rich.live import Live # type: ignore   
    from rich.panel import Panel # type: ignore
    from rich.text import Text # type: ignore
    from rich.prompt import Prompt # type: ignore
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback if Rich is not installed yet
    class Console:
        def print(self, *args, **kwargs): print(*args)
        def input(self, *args, **kwargs): return input(*args)
    
    class Prompt:
        @staticmethod
        def ask(*args, **kwargs): return input(*args)

from charlie.ui.components import (
    create_chat_bubble, 
    create_thinking_indicator,
    create_error_panel
)

class ChatCommand:
    """Handles text-based chat interactions with Charlie"""
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.console = Console()
        self.history: List[Dict[str, Any]] = []
        self.session_id = datetime.now().isoformat()
    
    async def start_chat(self):
        """Start interactive chat session"""
        
        self.console.print(Panel(
            "💬 Starting chat session with Charlie\nType 'exit' to quit, 'clear' to clear history",
            title="[bold green]Chat Mode[/bold green]",
            border_style="green"
        ))
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    self.console.print("[yellow]Chat session ended. Goodbye! 👋[/yellow]")
                    break
                elif user_input.lower() == 'clear':
                    self.history.clear()
                    self.console.print("[green]Chat history cleared[/green]")
                    continue
                elif user_input.lower() == 'history':
                    self.show_history()
                    continue
                elif not user_input.strip():
                    continue
                
                # Process the message
                await self.process_message(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Chat interrupted. Type 'exit' to quit.[/yellow]")
            except EOFError:
                break
    
    async def process_message(self, message: str) -> Optional[str]:
        """Process a single message and return response"""
        
        # Show thinking indicator
        with Live(create_thinking_indicator(), refresh_per_second=4) as live:
            try:
                # Make API call to backend
                response = await self.call_api(message)
                live.stop()
                
                if response:
                    # Display response
                    self.console.print(create_chat_bubble(response, is_user=False))
                    
                    # Save to history
                    self.add_to_history(message, response)
                    
                    return response
                else:
                    live.stop()
                    self.console.print(create_error_panel("No response from Charlie"))
                    
            except Exception as e:
                live.stop()
                error_msg = f"Error communicating with Charlie: {str(e)}"
                self.console.print(create_error_panel(error_msg))
                
                # Fallback response
                fallback_response = await self.get_fallback_response(message)
                if fallback_response:
                    self.console.print(create_chat_bubble(fallback_response, is_user=False))
                    return fallback_response
        
        return None
    
    async def call_api(self, message: str) -> Optional[str]:
        """Make API call to Charlie backend"""
        
        try:
            backend_url = self.ctx.config.get('backend_url')
            timeout = self.ctx.config.get('timeout')
            
            payload = {
                'message': message,
                'session_id': self.session_id,
                'history': self.history[-5:] if self.history else []  # Last 5 messages for context
            }
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Charlie-CLI/1.0'
            }
            
            # Add auth headers if available
            if self.ctx.config.get('supabase_key'):
                headers['Authorization'] = f"Bearer {self.ctx.config.get('supabase_key')}"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(
                    f"{backend_url}/api/v1/chat",
                    json=payload,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data.get('response', '')
                    elif response.status == 401:
                        return "Authentication failed. Please check your API keys."
                    elif response.status == 429:
                        return "Rate limit exceeded. Please wait a moment and try again."
                    else:
                        error_text = await response.text()
                        return f"API Error ({response.status}): {error_text}"
                        
        except asyncio.TimeoutError:
            return "Request timed out. Charlie might be busy thinking..."
        except aiohttp.ClientError as e:
            return f"Connection error: {str(e)}"
        except Exception as e:
            if self.ctx.debug:
                return f"Unexpected error: {str(e)}"
            return "Something went wrong. Try again later."
    
    async def get_fallback_response(self, message: str) -> Optional[str]:
        """Generate fallback response when API is unavailable"""
        
        # Simple keyword-based responses
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm Charlie, but I'm having trouble connecting to my brain right now. Please check your configuration."
        
        elif any(word in message_lower for word in ['help', 'what can you do']):
            return """I'm Charlie, your AI assistant. I can help with:
            
• Answering questions and having conversations
• Managing tasks and automation  
• Voice interaction
• File operations
• Email and calendar management

Right now I'm having connection issues. Please check:
1. Your internet connection
2. Backend server is running
3. API keys are configured correctly

Use 'charlie config show' to check your settings."""
        
        elif any(word in message_lower for word in ['error', 'problem', 'issue']):
            return """I'm experiencing connectivity issues. Here's what you can try:

1. Check if the backend server is running: `charlie status`
2. Verify your configuration: `charlie config show`  
3. Test your internet connection
4. Make sure your API keys are set up correctly

If problems persist, try running with --debug flag for more details."""
        
        else:
            return "I'm sorry, but I can't process your request right now due to connectivity issues. Please check your configuration and try again."
    
    def add_to_history(self, user_message: str, ai_response: str):
        """Add conversation to history"""
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response,
            'session_id': self.session_id
        }
        
        self.history.append(entry)
        
        # Keep history within limits
        max_entries = self.ctx.config.get('max_history_entries')
        if len(self.history) > max_entries:
            self.history = self.history[-max_entries:]
    
    def show_history(self):
        """Display conversation history"""
        
        if not self.history:
            self.console.print("[yellow]No conversation history yet[/yellow]")
            return
        
        self.console.print(Panel(
            f"Showing last {len(self.history)} messages from this session",
            title="[bold cyan]Chat History[/bold cyan]",
            border_style="cyan"
        ))
        
        for entry in self.history[-10:]:  # Show last 10
            timestamp = entry['timestamp'][:19] if self.ctx.config.get('show_timestamps') else ""
            
            if timestamp:
                self.console.print(f"[dim]{timestamp}[/dim]")
            
            self.console.print(create_chat_bubble(entry['user_message'], is_user=True))
            self.console.print(create_chat_bubble(entry['ai_response'], is_user=False))
            self.console.print()  # Empty line for spacing 