# 🛠️ Charlie Tech Stack

## 📋 Technology Stack Overview

This document outlines the complete technology stack for Charlie, organized by system components and deployment targets.

## 🎤 Voice Processing Layer

### Speech-to-Text (STT)
- **Primary**: Google Cloud Speech-to-Text API
  - Real-time streaming recognition
  - Multiple language support
  - Enhanced model for voice commands
  - Noise cancellation and adaptation

### Text-to-Speech (TTS)
- **Primary**: Google Cloud Text-to-Speech API
  - WaveNet voices for natural speech
  - SSML support for expression control
  - Voice customization options
  - Multiple accent support

### Audio Processing
- **Windows**: Windows Audio Session API (WASAPI)
- **Cross-platform**: PyAudio with PortAudio
- **Real-time processing**: librosa, soundfile
- **Wake word detection**: Porcupine (Picovoice)

## 🧠 AI & Machine Learning

### Large Language Model
- **Primary**: Google Gemini 2.5 Pro API
  - 1M+ token context window
  - Multimodal capabilities (text, image, document)
  - Function calling and tool use
  - Advanced reasoning and planning

### Supporting AI Services
- **Image Analysis**: Gemini Vision capabilities
- **Document Processing**: Gemini document understanding
- **Web Scraping**: Beautiful Soup + Gemini analysis
- **Local ML**: TensorFlow Lite (for offline features)

## 💾 Data & Memory Layer

### Primary Database
- **Supabase PostgreSQL**
  - User profiles and preferences
  - Conversation history and context
  - Task execution logs
  - Personal knowledge base
  - Reminders and scheduled tasks

### Supabase Features Used
- **Database**: PostgreSQL with Row Level Security (RLS)
- **Authentication**: Supabase Auth with OAuth providers
- **Real-time**: WebSocket subscriptions for live updates
- **Storage**: File storage for voice recordings and documents
- **Edge Functions**: Server-side logic for complex operations

### Caching & Performance
- **Redis**: Session caching and rate limiting
- **Local Storage**: Temporary file storage
- **Browser Storage**: Web app state persistence

## ⚙️ Backend Architecture

### Core Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Async Processing**: asyncio, aiohttp
- **Task Queue**: Celery with Redis broker
- **Process Management**: uvicorn + gunicorn

### API & Integration Layer
- **API Framework**: FastAPI with OpenAPI documentation
- **Authentication**: Supabase JWT tokens
- **Rate Limiting**: slowapi (FastAPI rate limiter)
- **CORS**: FastAPI CORS middleware
- **Validation**: Pydantic models

### Task Execution Engine
- **Script Runtime**: Python subprocess with sandboxing
- **Security**: Restricted execution environment
- **File System**: Secure temporary directories
- **Process Monitoring**: psutil for resource management

## 🖥️ Frontend Platforms

### Web Application
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand
- **Real-time**: Supabase Realtime subscriptions
- **Audio**: Web Audio API, MediaRecorder API

### Desktop Application
- **Framework**: Electron
- **Renderer**: React with TypeScript
- **Main Process**: Node.js with native modules
- **UI Components**: Same as web (Tailwind + shadcn/ui)
- **System Integration**: Native Windows APIs

### CLI Application
- **Language**: Python
- **Framework**: Click + Rich for enhanced CLI
- **Configuration**: YAML/TOML config files
- **Voice Integration**: Direct Python audio libraries
- **Output**: Rich console output with animations

## 🔧 Development & DevOps

### Development Environment
- **Windows 11**: Primary development target
- **Package Manager**: 
  - Python: Poetry
  - Node.js: pnpm
  - Global: Chocolatey (Windows)
- **Code Quality**: 
  - Python: Black, isort, flake8, mypy
  - TypeScript: ESLint, Prettier
- **Testing**:
  - Python: pytest, pytest-asyncio
  - JavaScript: Jest, React Testing Library

### Build & Deployment
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Cloud Platform**: 
  - Supabase (Database, Auth, Storage)
  - Google Cloud (AI APIs)
  - Vercel (Web app deployment)
- **Monitoring**: Sentry for error tracking

## 📦 Dependencies Management

### Python Backend Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = "^0.24.0"
supabase = "^2.0.0"
google-cloud-speech = "^2.22.0"
google-cloud-texttospeech = "^2.16.0"
google-generativeai = "^0.3.0"
pyaudio = "^0.2.11"
pydantic = "^2.5.0"
celery = "^5.3.0"
redis = "^5.0.0"
```

### Frontend Dependencies
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "typescript": "^5.2.0",
    "@supabase/supabase-js": "^2.38.0",
    "tailwindcss": "^3.3.0",
    "@radix-ui/react-*": "*",
    "zustand": "^4.4.0",
    "framer-motion": "^10.16.0"
  }
}
```

## 🔐 Security Stack

### Authentication & Authorization
- **Primary**: Supabase Auth (JWT)
- **OAuth Providers**: Google, GitHub, Microsoft
- **MFA**: TOTP support via Supabase
- **Session Management**: Secure cookie handling

### Data Security
- **Encryption**: AES-256 for sensitive data
- **API Security**: Rate limiting, CORS, HTTPS only
- **Database**: Row Level Security (RLS) policies
- **Local Storage**: Encrypted local configuration

### Infrastructure Security
- **Secrets Management**: Environment variables + Supabase Vault
- **Network**: VPC, firewall rules
- **Compliance**: GDPR compliance for user data

## 📊 Monitoring & Analytics

### Application Monitoring
- **Error Tracking**: Sentry
- **Performance**: Native platform metrics
- **Usage Analytics**: Supabase Analytics
- **Voice Metrics**: Custom metrics for STT/TTS performance

### Infrastructure Monitoring
- **Database**: Supabase built-in monitoring
- **API Performance**: FastAPI metrics
- **Resource Usage**: System metrics collection

## 🔄 Integration APIs

### External Services
- **Google Cloud AI**: Gemini, STT, TTS APIs
- **Email**: SMTP via Gmail API
- **Calendar**: Google Calendar API
- **Weather**: OpenWeatherMap API
- **News**: NewsAPI
- **File Storage**: Supabase Storage

### Local System Integration
- **Windows APIs**: Win32 for system control
- **File System**: Secure file operations
- **Process Management**: Application launching and control
- **Notifications**: Windows Toast notifications

---

## 🚀 Getting Started

See [ROADMAP.md](./ROADMAP.md) for implementation phases and [BACKEND_STRUCTURE.md](./BACKEND_STRUCTURE.md) for detailed backend architecture. 