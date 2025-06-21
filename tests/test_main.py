"""
Basic tests for the main Charlie application
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Charlie AI Assistant API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "online"


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


def test_docs_endpoint():
    """Test that API docs are accessible in debug mode"""
    # Note: This test assumes DEBUG=True
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Test that OpenAPI schema is available"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Charlie AI Assistant API"
    assert data["info"]["version"] == "1.0.0"


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_login_endpoint_exists(self):
        """Test that login endpoint exists and returns proper error for invalid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        # Should return 401 for invalid credentials or 500 if Supabase not configured
        assert response.status_code in [401, 500]
    
    def test_register_endpoint_exists(self):
        """Test that register endpoint exists"""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        })
        # Should return 400/500 if Supabase not configured properly
        assert response.status_code in [400, 500]


class TestAPIEndpoints:
    """Test API endpoint availability"""
    
    def test_voice_endpoints_exist(self):
        """Test that voice endpoints are properly configured"""
        # Test without authentication (should return 401/403)
        response = client.post("/api/v1/voice/stt", json={
            "audio_data": "fake_audio_data",
            "sample_rate": 16000,
            "encoding": "LINEAR16"
        })
        assert response.status_code in [401, 403, 422]  # Unauthorized or validation error
    
    def test_ai_endpoints_exist(self):
        """Test that AI endpoints are properly configured"""
        response = client.post("/api/v1/ai/chat", json={
            "message": "Hello",
            "session_id": "test"
        })
        assert response.status_code in [401, 403, 422]  # Unauthorized or validation error
    
    def test_memory_endpoints_exist(self):
        """Test that memory endpoints are properly configured"""
        response = client.get("/api/v1/memory/context")
        assert response.status_code in [401, 403]  # Unauthorized
    
    def test_task_endpoints_exist(self):
        """Test that task endpoints are properly configured"""
        response = client.get("/api/v1/tasks/types")
        assert response.status_code in [401, 403]  # Unauthorized


@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection (simplified)"""
    from app.core.database import get_supabase_client
    
    try:
        client = get_supabase_client()
        # Just test that we can create a client
        assert client is not None
    except Exception:
        # If Supabase credentials not configured, test should still pass
        pytest.skip("Supabase not configured for testing")


def test_configuration_loading():
    """Test that configuration loads properly"""
    from app.core.config import settings
    
    assert settings is not None
    assert hasattr(settings, 'DEBUG')
    assert hasattr(settings, 'SECRET_KEY')
    assert hasattr(settings, 'SUPABASE_URL')
    assert hasattr(settings, 'GEMINI_API_KEY') 