# Charlie - Voice-Controlled AI Assistant

> *"Sometimes you gotta run before you can walk."* - Tony Stark

## 🚀 Project Synopsis

Charlie is a sophisticated, real-time voice-controlled AI assistant inspired by Tony Stark's J.A.R.V.I.S., powered by Google Gemini 2.5 Pro. It combines natural conversation capabilities with intelligent task execution and rich multimodal reasoning to create a seamless digital assistant experience.

### 🎯 Vision

To create an intelligent, context-aware AI assistant that can understand, remember, and execute complex tasks through natural voice interaction, making technology more accessible and intuitive for everyday use.

### 🌟 Key Highlights

- **Voice-First Interaction**: Wake word activation ("Hey Charlie") with Google STT/TTS
- **Advanced AI Reasoning**: Powered by Gemini 2.5 Pro with 1M-token context window
- **Persistent Memory**: Supabase-powered memory system for user preferences and history
- **Multimodal Understanding**: Process images, documents, and web content
- **Secure Task Automation**: Execute local Python scripts safely
- **Cross-Platform**: CLI, Desktop (Electron), and Web (Next.js) interfaces

### 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Voice Layer   │────│   AI Brain      │────│  Memory Layer   │
│  (STT/TTS)      │    │ (Gemini 2.5)    │    │  (Supabase)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │            Interface Layer                      │
         │  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
         │  │   CLI   │  │ Desktop │  │   Web App       │ │
         │  │         │  │(Electron)│  │ (Next.js)      │ │
         │  └─────────┘  └─────────┘  └─────────────────┘ │
         └─────────────────────────────────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │         Task Execution Layer                    │
         │        (Python Scripts & APIs)                 │
         └─────────────────────────────────────────────────┘
```

### 🎯 Core Objectives

1. **Seamless Voice Interaction**: Enable natural, conversational AI with minimal friction
2. **Intelligent Task Automation**: Perform complex tasks through voice commands
3. **Persistent Learning**: Remember user preferences, habits, and context across sessions
4. **Secure Execution**: Safely execute local commands while maintaining security
5. **Multimodal Intelligence**: Understand and process various content types
6. **Cross-Platform Consistency**: Deliver uniform experience across all interfaces

### 🔐 Security & Privacy

- Local voice processing where possible
- Secure API communication with Gemini
- Encrypted data storage in Supabase
- Sandboxed script execution
- User consent for all data collection

### 📊 Success Metrics

- Voice recognition accuracy > 95%
- Task completion rate > 90%
- Average response time < 2 seconds
- User satisfaction score > 4.5/5
- Cross-platform feature parity

---

For detailed implementation guides, see:
- [Tech Stack](./TECH_STACK.md)
- [Project Roadmap](./ROADMAP.md)
- [Backend Structure](./BACKEND_STRUCTURE.md)
- [Frontend Guidelines](./FRONTEND_GUIDELINES.md) 