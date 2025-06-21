"""
Command history management for Charlie CLI
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class HistoryManager:
    """Manages command and conversation history"""
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.history_dir = Path.home() / '.charlie' / 'history'
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.command_history_file = self.history_dir / 'commands.json'
        self.chat_history_file = self.history_dir / 'conversations.json'
        
        self.command_history: List[Dict[str, Any]] = []
        self.chat_history: List[Dict[str, Any]] = []
        
        self.load_history()
    
    def load_history(self):
        """Load history from files"""
        
        try:
            # Load command history
            if self.command_history_file.exists():
                with open(self.command_history_file, 'r') as f:
                    self.command_history = json.load(f)
            
            # Load chat history
            if self.chat_history_file.exists():
                with open(self.chat_history_file, 'r') as f:
                    self.chat_history = json.load(f)
                    
        except Exception as e:
            if self.ctx.debug:
                print(f"Error loading history: {e}")
    
    def save_history(self):
        """Save history to files"""
        
        if not self.ctx.config.get('auto_save_history'):
            return
        
        try:
            # Save command history
            with open(self.command_history_file, 'w') as f:
                json.dump(self.command_history[-1000:], f, indent=2)  # Keep last 1000
            
            # Save chat history
            with open(self.chat_history_file, 'w') as f:
                json.dump(self.chat_history[-500:], f, indent=2)  # Keep last 500
                
        except Exception as e:
            if self.ctx.debug:
                print(f"Error saving history: {e}")
    
    def add_command(self, command: str, success: bool = True, output: str = ""):
        """Add command to history"""
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'success': success,
            'output': output[:500] if output else "",  # Truncate long output
            'session_id': getattr(self.ctx, 'session_id', 'unknown')
        }
        
        self.command_history.append(entry)
        
        # Keep within limits
        max_entries = self.ctx.config.get('max_history_entries', 100)
        if len(self.command_history) > max_entries:
            self.command_history = self.command_history[-max_entries:]
        
        self.save_history()
    
    def add_conversation(self, user_message: str, ai_response: str, session_id: str = None):
        """Add conversation to history"""
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response,
            'session_id': session_id or getattr(self.ctx, 'session_id', 'unknown'),
            'message_length': len(user_message),
            'response_length': len(ai_response)
        }
        
        self.chat_history.append(entry)
        
        # Keep within limits
        max_entries = self.ctx.config.get('max_history_entries', 100)
        if len(self.chat_history) > max_entries:
            self.chat_history = self.chat_history[-max_entries:]
        
        self.save_history()
    
    def get_recent_commands(self, limit: int = 10) -> List[str]:
        """Get recent commands for command completion"""
        
        return [entry['command'] for entry in self.command_history[-limit:]]
    
    def get_command_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get command history"""
        
        return self.command_history[-limit:] if self.command_history else []
    
    def get_chat_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history"""
        
        return self.chat_history[-limit:] if self.chat_history else []
    
    def search_history(self, query: str, history_type: str = 'both') -> List[Dict[str, Any]]:
        """Search through history"""
        
        results = []
        query_lower = query.lower()
        
        if history_type in ['both', 'commands']:
            for entry in self.command_history:
                if query_lower in entry['command'].lower():
                    results.append({**entry, 'type': 'command'})
        
        if history_type in ['both', 'chat']:
            for entry in self.chat_history:
                if (query_lower in entry['user_message'].lower() or 
                    query_lower in entry['ai_response'].lower()):
                    results.append({**entry, 'type': 'chat'})
        
        # Sort by timestamp (most recent first)
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return results[:50]  # Limit results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get history statistics"""
        
        stats = {
            'total_commands': len(self.command_history),
            'total_conversations': len(self.chat_history),
            'successful_commands': sum(1 for cmd in self.command_history if cmd['success']),
            'failed_commands': sum(1 for cmd in self.command_history if not cmd['success'])
        }
        
        if self.chat_history:
            stats['avg_message_length'] = sum(conv['message_length'] for conv in self.chat_history) / len(self.chat_history)
            stats['avg_response_length'] = sum(conv['response_length'] for conv in self.chat_history) / len(self.chat_history)
            stats['first_conversation'] = self.chat_history[0]['timestamp']
            stats['last_conversation'] = self.chat_history[-1]['timestamp']
        
        if self.command_history:
            stats['first_command'] = self.command_history[0]['timestamp']
            stats['last_command'] = self.command_history[-1]['timestamp']
            
            # Most used commands
            command_counts = {}
            for cmd in self.command_history:
                base_cmd = cmd['command'].split()[0] if cmd['command'] else 'unknown'
                command_counts[base_cmd] = command_counts.get(base_cmd, 0) + 1
            
            stats['most_used_commands'] = sorted(
                command_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        
        return stats
    
    def clear_history(self, history_type: str = 'both'):
        """Clear history"""
        
        if history_type in ['both', 'commands']:
            self.command_history.clear()
            if self.command_history_file.exists():
                self.command_history_file.unlink()
        
        if history_type in ['both', 'chat']:
            self.chat_history.clear()
            if self.chat_history_file.exists():
                self.chat_history_file.unlink()
        
        self.save_history()
    
    def export_history(self, output_file: str, history_type: str = 'both'):
        """Export history to file"""
        
        export_data = {}
        
        if history_type in ['both', 'commands']:
            export_data['commands'] = self.command_history
        
        if history_type in ['both', 'chat']:
            export_data['conversations'] = self.chat_history
        
        export_data['exported_at'] = datetime.now().isoformat()
        export_data['charlie_version'] = getattr(self.ctx, 'version', '1.0.0')
        
        try:
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            return True
        except Exception:
            return False
    
    def import_history(self, input_file: str) -> bool:
        """Import history from file"""
        
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            if 'commands' in data:
                self.command_history.extend(data['commands'])
            
            if 'conversations' in data:
                self.chat_history.extend(data['conversations'])
            
            self.save_history()
            return True
            
        except Exception:
            return False 