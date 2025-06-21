# Charlie AI Assistant Backend

> Phase 1 Implementation Complete ✅

This is the backend implementation for Charlie, a sophisticated voice-controlled AI assistant powered by Google Gemini 2.5 Pro.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Docker (optional, for containerized development)
- Supabase account and project
- Google Cloud account with Gemini API access

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd charlie
   python scripts/setup.py
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start development server**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

4. **Access API documentation**:
   - OpenAPI docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🏗️ Architecture

### Core Components

```
app/
├── main.py                 # FastAPI application entry point
├── core/                   # Core utilities
│   ├── config.py          # Configuration management
│   ├── database.py        # Supabase client
│   ├── security.py        # Authentication & authorization
│   └── exceptions.py      # Custom exceptions
├── api/v1/                # API endpoints
│   ├── endpoints/         # Route handlers
│   └── router.py          # Main API router
├── services/              # Business logic
│   ├── voice/             # STT, TTS, voice processing
│   ├── ai/                # Gemini AI integration
│   └── memory/            # Context & memory management
└── models/                # Data models
    ├── database/          # Database models
    └── schemas/           # API schemas
```

### Key Features

✅ **Authentication System**
- Supabase Auth integration
- JWT token management
- User registration/login

✅ **Voice Processing**
- Google Cloud STT integration
- Google Cloud TTS integration
- Complete voice command pipeline

✅ **AI Brain**
- Gemini 2.5 Pro integration
- Context-aware conversations
- Memory management

✅ **Database Layer**
- Supabase PostgreSQL
- Row Level Security (RLS)
- User data management

✅ **API Endpoints**
- RESTful API design
- Rate limiting
- Comprehensive documentation

## 🔧 Configuration

### Environment Variables

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Google Cloud
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_APPLICATION_CREDENTIALS=./google-credentials.json

# Voice Settings
STT_LANGUAGE_CODE=en-US
TTS_VOICE_NAME=en-US-Neural2-F

# Security
SECRET_KEY=your-secret-key
```

### Database Setup

1. **Create Supabase project**
2. **Run database migrations**:
   ```python
   from app.core.database import create_database_schema
   await create_database_schema()
   ```

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/auth/me` - Current user info

### Voice Processing
- `POST /api/v1/voice/command` - Complete voice command
- `POST /api/v1/voice/stt` - Speech-to-text
- `POST /api/v1/voice/tts` - Text-to-speech
- `GET /api/v1/voice/capabilities` - Voice capabilities

### AI Processing
- `POST /api/v1/ai/chat` - Chat completion
- `POST /api/v1/ai/generate` - Generate response
- `POST /api/v1/ai/multimodal` - Multimodal analysis

### Memory Management
- `GET /api/v1/memory/context` - User context
- `GET /api/v1/memory/search` - Search memories
- `PUT /api/v1/memory/preferences` - Update preferences

### Task Management
- `POST /api/v1/tasks/execute` - Execute task
- `GET /api/v1/tasks/status/{id}` - Task status
- `GET /api/v1/tasks/history` - Task history

## 🧪 Testing

### Run Tests
```bash
# All tests and quality checks
python scripts/run_tests.py

# Unit tests only
poetry run pytest tests/ -v

# With coverage
poetry run pytest tests/ --cov=app --cov-report=html
```

### Code Quality
```bash
# Format code
poetry run black app/ tests/
poetry run isort app/ tests/

# Lint code
poetry run flake8 app/ tests/
poetry run mypy app/
```

## 🐳 Docker Development

### Using Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f charlie-backend

# Stop services
docker-compose down
```

### Services
- **charlie-backend**: Main API server (port 8000)
- **redis**: Cache and task queue (port 6379)
- **celery-worker**: Background task processor

## 🔐 Security

### Features
- JWT-based authentication
- Row Level Security (RLS) in database
- Rate limiting on all endpoints
- Input validation and sanitization
- Secure environment variable management

### Best Practices
- Use strong secret keys
- Enable HTTPS in production
- Regular security audits
- Principle of least privilege

## 📈 Performance

### Optimizations
- Async/await throughout
- Connection pooling
- Redis caching
- Rate limiting
- Efficient database queries

### Monitoring
- Structured logging
- Health check endpoints
- Performance metrics
- Error tracking

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=false`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure production database
- [ ] Set up HTTPS
- [ ] Configure monitoring
- [ ] Set up backups

### Environment Setup
```bash
# Production dependencies only
poetry install --no-dev

# Run with production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🔄 Development Workflow

### Making Changes
1. Create feature branch
2. Make changes
3. Run tests: `python scripts/run_tests.py`
4. Create pull request

### Adding New Features
1. Update models if needed
2. Add service layer logic
3. Create API endpoints
4. Add tests
5. Update documentation

## 📚 Phase 1 Completion Status

### ✅ Completed Milestones

**Sprint 1-2: Project Setup & Core Infrastructure**
- [x] Development environment setup
- [x] FastAPI backend framework with basic API structure
- [x] Supabase client configuration
- [x] Environment variables management
- [x] Basic middleware (CORS, security headers)
- [x] API documentation setup (OpenAPI)
- [x] Testing framework setup (pytest)
- [x] Database schema design
- [x] Basic authentication system with Supabase Auth
- [x] Docker containerization

**Sprint 3: Voice Processing Foundation**
- [x] Google STT integration for voice input
- [x] Google TTS integration for voice output
- [x] Audio processing pipeline setup
- [x] Basic voice command recognition
- [x] Audio file handling and storage

### 📋 Phase 1 Deliverables
- [x] Working development environment
- [x] Basic FastAPI server with health checks
- [x] Supabase database with initial schema
- [x] Authentication endpoints
- [x] Docker compose setup for local development
- [x] Voice processing services
- [x] AI integration with Gemini
- [x] Memory management system
- [x] Task execution framework
- [x] Comprehensive API documentation

## 📞 Support

For questions or issues:
1. Check the API documentation at `/docs`
2. Review the logs for errors
3. Consult the configuration guide
4. Check Supabase and Google Cloud status

## 🎯 Next Steps (Phase 2)

- Enhanced task automation capabilities
- Advanced memory and context management
- Real-time voice streaming
- Performance optimizations
- Advanced security features

---

**Phase 1 Status**: ✅ **COMPLETE**  
**Ready for**: Phase 2 development and frontend integration 