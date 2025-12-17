"""
Job Fetcher Stack - JWT Authentication
"""
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import get_settings
from pydantic import BaseModel
from typing import Optional


security = HTTPBearer()


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # user_id
    email: Optional[str] = None
    role: Optional[str] = "user"
    exp: int


class CurrentUser(BaseModel):
    """Current authenticated user."""
    user_id: str
    email: Optional[str] = None
    role: str = "user"


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> CurrentUser:
    """
    Verify JWT token and return current user.
    Used as a dependency in protected routes.
    """
    settings = get_settings()
    token = credentials.credentials
    
    # In DEV_MODE, accept a mock token for testing
    if settings.dev_mode and token == "dev-token":
        return CurrentUser(
            user_id="7ee1c8ec-27c1-4ea6-90ac-9e028572ecf4",
            email="dev@example.com",
            role="user"
        )
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False}  # Supabase doesn't always include aud
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")
        
        return CurrentUser(
            user_id=user_id,
            email=payload.get("email"),
            role=payload.get("role", "user")
        )
        
    except JWTError as e:
        raise HTTPException(
            status_code=401, 
            detail=f"Invalid token: {str(e)}"
        )


async def get_current_user(
    current_user: CurrentUser = Depends(verify_token)
) -> CurrentUser:
    """Dependency to get the current authenticated user."""
    return current_user


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Dependency to require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user
