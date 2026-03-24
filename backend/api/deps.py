"""
Shared dependencies for API routes.
JWT token creation and validation.
"""

import os
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.user import User
from services.auth_service import AuthService

# JWT Config
SECRET_KEY = os.getenv("JWT_SECRET", "agentichire-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer()

# Shared auth service instance
auth_service = AuthService()


def create_token(user: User) -> str:
    """Create a JWT token for a user."""
    payload = {
        "sub": user.id,
        "username": user.username,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Validate JWT token and return the current user."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Find user in the JSON database
    users = auth_service._load_users()
    for u_data in users:
        if u_data.get("id") == user_id:
            return User(**u_data)

    raise HTTPException(status_code=401, detail="User not found")
