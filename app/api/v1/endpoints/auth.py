"""
Authentication endpoints
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.core.security import security_manager, get_current_user
from app.models.schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse, 
    RefreshTokenRequest, UserInfo, LogoutRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: LoginRequest):
    """User login endpoint"""
    try:
        response = await security_manager.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Extract token information from Supabase response
        session = response.session
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
        
        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            expires_in=session.expires_in or 3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/register", response_model=TokenResponse)
@limiter.limit("3/minute")
async def register(request: RegisterRequest):
    """User registration endpoint"""
    try:
        response = await security_manager.register_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
        
        session = response.session
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed - no session created"
            )
        
        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            expires_in=session.expires_in or 3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token"""
    try:
        response = await security_manager.refresh_token(request.refresh_token)
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        session = response.session
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
        
        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            expires_in=session.expires_in or 3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """User logout endpoint"""
    try:
        # Extract token from current user context (this is simplified)
        success = await security_manager.logout_user("")
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logout failed"
            )
        
        return {"message": "Logout successful"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current user information"""
    try:
        return UserInfo(
            id=current_user["id"],
            email=current_user["email"],
            full_name=current_user.get("user_metadata", {}).get("full_name"),
            email_verified=current_user.get("email_confirmed_at") is not None,
            created_at=current_user.get("created_at", "")
        )
        
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.get("/verify")
async def verify_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Verify token validity"""
    return {
        "valid": True,
        "user_id": current_user["id"],
        "email": current_user["email"]
    } 