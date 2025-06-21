"""
Security utilities for Charlie AI Assistant
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    
    try:
        # First try to verify with Supabase
        supabase = get_supabase_client()
        user = supabase.auth.get_user(token)
        return user.user
        
    except Exception:
        # Fallback to local JWT verification
        try:
            payload = verify_token(token)
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                )
            return {"id": user_id, "email": payload.get("email")}
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user (additional validation can be added here)"""
    return current_user


def require_auth(func):
    """Decorator to require authentication for endpoints"""
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user")
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        return await func(*args, **kwargs)
    return wrapper


class SecurityManager:
    """Security manager for handling various security operations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    async def register_user(self, email: str, password: str, full_name: str = None) -> Optional[Dict[str, Any]]:
        """Register a new user"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })
            return response
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token"""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            return response
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None
    
    async def logout_user(self, access_token: str) -> bool:
        """Logout user and invalidate token"""
        try:
            self.supabase.auth.sign_out()
            return True
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False


# Global security manager instance
security_manager = SecurityManager() 