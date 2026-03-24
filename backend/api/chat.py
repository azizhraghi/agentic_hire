"""
Chat API Route
POST /api/chat — Send a message, detect intent, return response
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from backend.api.deps import get_current_user
from models.user import User
from agents.core.orchestrator import Orchestrator

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    workspace: Optional[str] = None  # "entrepreneur", "student", or None


@router.post("", response_model=ChatResponse)
def send_message(req: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    Send a chat message. The orchestrator detects intent and returns a response
    along with the detected workspace type.
    """
    orch = Orchestrator()
    orch.set_user(current_user)

    response_text = orch.handle_request(req.message, current_user.id)

    # Detect workspace from response (same logic as app.py)
    workspace = None
    lower_resp = response_text.lower()
    if "recruteur" in lower_resp:
        workspace = "entrepreneur"
    elif "candidat" in lower_resp:
        workspace = "student"

    return ChatResponse(response=response_text, workspace=workspace)
