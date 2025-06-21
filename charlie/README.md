# Charlie CLI - Voice-Controlled AI Assistant

## 🚀 Quick Start

### Installation
```bash
# Install using pip
pip install charlie-cli

# Or clone and install locally
git clone <repo>
cd charlie
pip install -e .
```

### First Run
```bash
# Run setup wizard
charlie config setup

# Start interactive chat
charlie chat

# Voice interaction
charlie voice --listen

# Get help
charlie --help
```

## 📋 Commands

### Core Commands
```bash
charlie chat                    # Start text-based conversation
charlie voice --listen          # Start voice interaction
charlie voice --continuous      # Continuous listening mode
charlie config show            # Show configuration
charlie config set <key> <val> # Set configuration value
charlie status                 # Show system status
charlie history                # Show conversation history
charlie ask "question"         # Quick question
```

### Configuration
```bash
charlie config setup           # Interactive setup wizard
charlie config get <key>       # Get config value
charlie config set <key> <val> # Set config value
charlie config reset           # Reset to defaults
charlie config validate        # Validate configuration
```

### Advanced Usage
```bash
# Debug mode
charlie --debug chat

# Custom config file
charlie --config-file custom.yaml chat

# Voice system test
charlie voice test

# Export conversation history
charlie history export history.json
```

## ⚙️ Configuration

Charlie stores configuration in `~/.charlie/config.yaml`.

### Required Settings
```yaml
gemini_api_key: "your-gemini-api-key"
supabase_url: "your-supabase-url" 
supabase_key: "your-supabase-key"
```

### Voice Settings
```yaml
stt_language: "en-US"
tts_voice: "en-US-Neural2-F"
wake_word: "Hey Charlie"
voice_threshold: 0.5
```

### CLI Settings
```yaml
backend_url: "http://localhost:8000"
timeout: 30
auto_save_history: true
max_history_entries: 100
theme: "dark"
show_timestamps: true
```

## 🎤 Voice Features

### Wake Word Activation
- Say "Hey Charlie" to activate voice mode
- Configurable wake word detection
- Background listening support

### Voice Commands
- Natural speech recognition
- Multi-language support
- Noise cancellation
- Real-time transcription

### Text-to-Speech
- Natural voice responses
- Configurable voice selection
- Emotional expression support
- SSML markup support

## 🔧 Troubleshooting

### Common Issues

**Voice not working:**
```bash
# Test voice system
charlie voice test

# Check microphone
charlie config get voice_threshold

# Verify audio devices
python -c "import pyaudio; print('PyAudio available')"
```

**API errors:**
```bash
# Check configuration
charlie config validate

# Test backend connection
charlie status

# Verify API keys
charlie config show
```

**Installation issues:**
```bash
# Install dependencies
pip install rich click pyaudio google-cloud-speech

# Windows-specific
pip install pywin32
```

## 🔗 Integration

### Backend API
Charlie CLI connects to the FastAPI backend at `http://localhost:8000` by default.

Ensure the backend is running:
```bash
cd app
uvicorn main:app --reload
```

### Supabase Integration
- User authentication
- Conversation history
- Memory persistence
- Real-time updates

## 📊 Features

✅ **Implemented (Phase 4)**
- [x] Rich CLI interface with Click
- [x] Voice interaction in terminal  
- [x] Configuration management
- [x] CLI-specific optimizations
- [x] Command history and shortcuts
- [x] Interactive setup wizard
- [x] Multi-platform support
- [x] Error handling and fallbacks
- [x] Keyboard shortcuts
- [x] Real-time voice processing

🚧 **In Progress**
- [ ] Advanced voice commands
- [ ] Plugin system
- [ ] Custom themes
- [ ] Voice training
- [ ] Offline mode

## 🎯 Usage Examples

### Basic Chat
```bash
$ charlie chat
💬 Starting chat session with Charlie
Type 'exit' to quit, 'clear' to clear history

You: Hello Charlie!
Charlie: Hello! I'm Charlie, your AI assistant. How can I help you today?

You: What's the weather like?
Charlie: I'd be happy to help with weather information! Could you please tell me your location?
```

### Voice Interaction
```bash
$ charlie voice --listen
🎤 Voice interaction mode
Press SPACE to start recording, release to stop
Press ESC to exit

[Recording...] "Hey Charlie, what time is it?"
You said: Hey Charlie, what time is it?
Charlie: The current time is 2:30 PM Pacific Time.
```

### Configuration Setup
```bash
$ charlie config setup
Welcome to Charlie! Let's set up your configuration.

Step 1: API Configuration
Google Gemini API Key: [hidden input]
Supabase Project URL (optional): https://your-project.supabase.co
Supabase API Key: [hidden input]

Step 2: Voice Configuration  
Wake word for voice activation (Hey Charlie): Hey Charlie
Preferred language for voice (en-US): en-US

✅ Setup complete! Charlie is ready to use.
```

## 📚 API Reference

See the [Backend Structure](../BACKEND_STRUCTURE.md) documentation for API endpoints and integration details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details. 