# 🏗️ Charlie Backend Architecture

## 📋 Overview
The Charlie backend is built using FastAPI with a modular, scalable architecture designed for high-performance voice processing, AI integration, and secure task automation.

## 🗂️ Project Structure

```
charlie-backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── security.py         # Security utilities
│   │   ├── database.py         # Database connection
│   │   └── exceptions.py       # Custom exceptions
│   ├── api/v1/endpoints/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── voice.py           # Voice processing endpoints
│   │   ├── ai.py              # AI/Gemini endpoints
│   │   ├── tasks.py           # Task automation endpoints
│   │   └── memory.py          # Memory management endpoints
│   ├── services/
│   │   ├── voice/             # STT/TTS services
│   │   ├── ai/                # Gemini AI services
│   │   ├── memory/            # Memory management
│   │   ├── tasks/             # Task execution
│   │   └── auth/              # Authentication services
│   ├── models/
│   │   ├── database/          # Database models
│   │   └── schemas/           # API schemas
│   └── utils/                 # Utility functions
├── migrations/                # Database migrations
├── scripts/                   # Deployment scripts
├── docker/                    # Docker configuration
└── tests/                     # Test suites
```

## 🔧 Core Components

### 1. FastAPI Application (`main.py`)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title="Charlie AI Assistant API",
    description="Voice-controlled AI assistant",
    version="1.0.0"
)

app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_HOSTS)
app.include_router(api_router, prefix="/api/v1")
```

### 2. Configuration (`core/config.py`)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment
    DEBUG: bool = False
    SECRET_KEY: str
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Google Cloud
    GEMINI_API_KEY: str
    GOOGLE_APPLICATION_CREDENTIALS: str
    
    # Voice Settings
    STT_LANGUAGE_CODE: str = "en-US"
    TTS_VOICE_NAME: str = "en-US-Neural2-F"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 3. Service Architecture

#### Voice Service (`services/voice/stt_service.py`)
```python
import asyncio
from google.cloud import speech

class STTService:
    def __init__(self):
        self.client = speech.SpeechClient()
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=settings.STT_LANGUAGE_CODE,
        )
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        audio = speech.RecognitionAudio(content=audio_data)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, self.client.recognize, {"config": self.config, "audio": audio}
        )
        return response.results[0].alternatives[0].transcript if response.results else ""
```

#### AI Service (`services/ai/gemini_service.py`)
```python
import google.generativeai as genai
from app.services.memory.context_service import ContextService

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-pro")
        self.context_service = ContextService()
    
    async def generate_response(self, user_input: str, user_id: str) -> str:
        user_context = await self.context_service.get_user_context(user_id)
        prompt = self._build_prompt(user_input, user_context)
        response = await self.model.generate_content_async(prompt)
        
        await self.context_service.store_interaction(user_id, user_input, response.text)
        return response.text
```

### 4. Database Schema

```sql
-- Core Tables
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user_input TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    memory_type VARCHAR NOT NULL,
    content TEXT NOT NULL,
    importance INTEGER DEFAULT 1,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE task_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR NOT NULL,
    task_params JSONB NOT NULL,
    status VARCHAR NOT NULL,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 5. Security Implementation

#### Authentication (`services/auth/supabase_auth.py`)
```python
from supabase import create_client
from fastapi import HTTPException

class AuthService:
    def __init__(self):
        self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    async def verify_token(self, token: str):
        try:
            user = self.supabase.auth.get_user(token)
            return user
        except Exception:
            raise HTTPException(401, "Invalid token")
```

#### Task Security (`services/tasks/security.py`)
```python
import subprocess
import tempfile
from pathlib import Path

class SecureTaskExecutor:
    def __init__(self):
        self.allowed_commands = {'email', 'calendar', 'file_ops', 'app_control'}
        self.temp_dir = Path(tempfile.gettempdir()) / "charlie_tasks"
    
    async def execute_task(self, task_type: str, params: dict):
        if task_type not in self.allowed_commands:
            raise ValueError(f"Task type {task_type} not allowed")
        # Secure execution implementation
```

## 🚀 Deployment

### Docker Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup
```bash
# Install dependencies
pip install poetry
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
poetry run uvicorn app.main:app --reload
```

## 📝 Development Guidelines

### 1. Code Structure
- Follow FastAPI best practices
- Use dependency injection for services
- Implement proper error handling
- Add comprehensive logging

### 2. Testing Strategy
```bash
# Unit tests
poetry run pytest tests/unit/

# Integration tests
poetry run pytest tests/integration/

# Coverage report
poetry run pytest --cov=app --cov-report=html
```

### 3. Performance Optimization
- Use async/await for I/O operations
- Implement caching with Redis
- Optimize database queries
- Monitor API response times

---

This structure provides a solid foundation for Charlie's backend development. See [ROADMAP.md](./ROADMAP.md) for implementation phases and [FRONTEND_GUIDELINES.md](./FRONTEND_GUIDELINES.md) for frontend development. 