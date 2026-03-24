"""
Auth API Routes
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from backend.api.deps import auth_service, create_token, get_current_user
from models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# --- Request / Response Schemas ---

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user: dict

class UserResponse(BaseModel):
    id: str
    username: str
    role: Optional[str] = None
    email: Optional[str] = None


# --- Routes ---

@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """Register a new user and return a JWT token."""
    user = auth_service.register(req.username, req.password, req.email)
    if not user:
        raise HTTPException(status_code=400, detail="Username already exists")
    token = create_token(user)
    return AuthResponse(
        token=token,
        user={"id": user.id, "username": user.username, "role": user.role}
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """Login and return a JWT token."""
    user = auth_service.login(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user)
    return AuthResponse(
        token=token,
        user={"id": user.id, "username": user.username, "role": user.role}
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        email=current_user.email
    )
