# backend/src/auth/jwt_handler.py (simplified version)
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import base64
import json

SECRET_KEY = os.getenv("NEXTAUTH_SECRET", "your-secret-key")
ALGORITHM = "HS256"

def verify_nextauth_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify NextAuth.js JWT token."""
    try:
        # For development, we'll use a simple approach
        # In production, you'd properly verify the NextAuth JWT
        
        # Try to decode as base64 first (our simple token)
        try:
            decoded = base64.b64decode(token)
            payload = json.loads(decoded.decode('utf-8'))
            return payload
        except:
            pass
        
        # Try to decode as JWT
        try:
            payload = jwt.decode(
                token, 
                SECRET_KEY, 
                algorithms=[ALGORITHM],
                options={"verify_signature": False}  # Temporarily disable for development
            )
            return payload
        except:
            pass
            
        return None
        
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token for API authentication."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt