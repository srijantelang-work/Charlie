"""
Custom exceptions for Charlie AI Assistant
"""

from typing import Any, Dict, Optional


class CharlieException(Exception):
    """Base exception for Charlie AI Assistant"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(CharlieException):
    """Authentication related errors"""
    pass


class AuthorizationError(CharlieException):
    """Authorization related errors"""
    pass


class VoiceProcessingError(CharlieException):
    """Voice processing related errors"""
    pass


class AIServiceError(CharlieException):
    """AI service related errors"""
    pass


class TaskExecutionError(CharlieException):
    """Task execution related errors"""
    pass


class DatabaseError(CharlieException):
    """Database operation errors"""
    pass


class ConfigurationError(CharlieException):
    """Configuration related errors"""
    pass


class ValidationError(CharlieException):
    """Data validation errors"""
    pass


class RateLimitError(CharlieException):
    """Rate limiting errors"""
    pass


class ServiceUnavailableError(CharlieException):
    """Service unavailability errors"""
    pass 