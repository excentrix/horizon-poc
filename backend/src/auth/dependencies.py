# backend/src/auth/dependencies.py (update for Neon adapter compatibility)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .jwt_handler import verify_nextauth_token
from models.core import DatabaseService, User

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    try:
        token = credentials.credentials
        payload = verify_nextauth_token(token)
        
        if payload is None:
            raise credentials_exception
            
        # Try to get user ID from payload
        user_id = payload.get("sub") or payload.get("id")
        email = payload.get("email")
        
        if not user_id and not email:
            raise credentials_exception
            
    except Exception as e:
        print(f"Auth error: {e}")
        raise credentials_exception
    
    # Get user by ID first, then by email
    user = None
    if user_id:
        user = DatabaseService.get_user_by_id(user_id)
    
    if not user and email:
        user = DatabaseService.get_user_by_email(email)
    
    if not user:
        # Create user if doesn't exist (fallback)
        if email:
            user = DatabaseService.create_user(
                email=email,
                name=payload.get("name"),
                image=payload.get("image") or payload.get("picture")
            )
        else:
            raise credentials_exception
    
    return user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None