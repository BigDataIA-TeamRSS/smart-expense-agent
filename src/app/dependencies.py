"""Shared dependencies for FastAPI endpoints"""
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import hashlib

from src.core.database import get_database
from src.integrations.plaid_service import PlaidService

# Security scheme for Swagger UI - this will show the "Authorize" button
security = HTTPBearer()


def get_db():
    """Dependency to get database instance"""
    return get_database()


def get_plaid_service():
    """Dependency to get Plaid service"""
    return PlaidService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db = Depends(get_db)
):
    """
    Dependency to get current authenticated user.
    For now, uses simple token-based auth (can be upgraded to JWT later).
    Token format: username:password_hash
    
    In Swagger UI: Click "Authorize" button and enter: Bearer username:password_hash
    Example: Bearer somil:2251e058ec7837bc6a5f6c00a4b5df85ec3f2fa563e590d113826e3b3d40fbb0
    """
    # HTTPBearer automatically extracts the token from "Bearer <token>" format
    token = credentials.credentials
    
    # Simple token validation - token is username:password_hash
    # In production, replace with proper JWT validation
    try:
        if ":" in token:
            username, password_hash = token.split(":", 1)
            
            # Get user with password hash for authentication
            user = db.get_user_for_auth(username)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token"
                )
            
            # Verify password hash matches stored hash
            # Token format: username:SHA256(password)
            # Database stores: password_hash = SHA256(password) (in "password" field for JSON, "password_hash" for SQL)
            stored_hash = user.get("password_hash") or user.get("password")
            if stored_hash and stored_hash == password_hash:
                # Remove password from response
                user.pop("password", None)
                user.pop("password_hash", None)
                return user
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token"
                )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False)),
    db = Depends(get_db)
):
    """Optional authentication - returns None if not authenticated"""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
