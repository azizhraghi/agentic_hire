"""
Recruiter API Routes
POST /api/recruiter/generate-job
POST /api/recruiter/score-candidates
GET  /api/recruiter/offers
POST /api/recruiter/offers
"""

import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

from backend.api.deps import get_current_user
from models.user import User
from agents.entrepreneur.recruiter_agents import RecruiterCoordinator

router = APIRouter(prefix="/api/recruiter", tags=["Recruiter"])


# --- Request / Response Schemas ---

class GenerateJobRequest(BaseModel):
    description: str
    api_key: Optional[str] = None

class GenerateJobResponse(BaseModel):
    job_data: dict
    linkedin_post: str
    offer_id: str
    form_url: str

class CandidateInput(BaseModel):
    nom: str
    prenom: Optional[str] = ""
    email: Optional[str] = ""
    cv_text: str

class ScoreCandidatesRequest(BaseModel):
    candidates: List[CandidateInput]
    job_data: dict
    api_key: Optional[str] = None

class SaveOfferRequest(BaseModel):
    job_data: dict
    linkedin_post: str
    offer_id: str
    form_url: str


# --- Helper Functions ---

def _get_api_key(provided_key: Optional[str] = None) -> str:
    """Get API key from request or environment."""
    key = provided_key or os.getenv("MISTRAL_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise HTTPException(status_code=400, detail="No AI API key configured. Provide one or set MISTRAL_API_KEY env variable.")
    return key


def _load_user_offers(user_id: str) -> list:
    """Load all offers for a user."""
    fichier = f"data/{user_id}_data.json"
    if not os.path.exists(fichier):
        return []
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            content = json.load(f)
            if isinstance(content, list):
                flat = []
                for item in content:
                    if isinstance(item, list):
                        flat.extend(item)
                    else:
                        flat.append(item)
                return flat
            return [content]
    except Exception:
        return []


def _save_offer(user_id: str, job_data: dict, linkedin_post: str, offer_id: str, form_url: str):
    """Save offer to user's data file."""
    os.makedirs("data", exist_ok=True)
    fichier = f"data/{user_id}_data.json"

    enregistrement = {
        "id": None,
        "user_id": user_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type_flux": "entrepreneur",
        "data": job_data,
        "artifacts": {
            "offer_id": offer_id,
            "form_link": form_url,
            "linkedin_post": linkedin_post,
        },
    }

    historique = []
    if os.path.exists(fichier):
        with open(fichier, "r", encoding="utf-8") as f:
            contenu = json.load(f)
            historique = contenu if isinstance(contenu, list) else [contenu]

    enregistrement["id"] = len(historique) + 1
    historique.append(enregistrement)

    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(historique, f, indent=2, ensure_ascii=False)


# --- Routes ---

@router.post("/generate-job", response_model=GenerateJobResponse)
def generate_job(req: GenerateJobRequest, current_user: User = Depends(get_current_user)):
    """Generate a structured job description + LinkedIn post from natural language."""
    api_key = _get_api_key(req.api_key)

    coordinator = RecruiterCoordinator(api_key=api_key, use_mistral=True)

    offer_id = f"OFF-{int(datetime.now().timestamp())}"
    form_url = f"http://localhost:5173/apply?offer_id={offer_id}"

    result = coordinator.create_job_posting(raw_input=req.description, form_url=form_url)

    return GenerateJobResponse(
        job_data=result.get("job_data", {}),
        linkedin_post=result.get("linkedin_post", ""),
        offer_id=offer_id,
        form_url=form_url,
    )


@router.post("/score-candidates")
def score_candidates(req: ScoreCandidatesRequest, current_user: User = Depends(get_current_user)):
    """AI-score candidates against job requirements."""
    api_key = _get_api_key(req.api_key)

    coordinator = RecruiterCoordinator(api_key=api_key, use_mistral=True)

    candidates_dicts = [c.dict() for c in req.candidates]
    scored = coordinator.evaluate_candidates(candidates_dicts, req.job_data)
    scored_with_plans = coordinator.plan_interviews(scored, req.job_data)

    return {"scored_candidates": scored_with_plans}


@router.get("/offers")
def list_offers(current_user: User = Depends(get_current_user)):
    """List all saved offers for the current user."""
    offers = _load_user_offers(current_user.id)
    return {"offers": offers}


@router.post("/offers")
def save_offer_route(req: SaveOfferRequest, current_user: User = Depends(get_current_user)):
    """Save a generated offer."""
    _save_offer(current_user.id, req.job_data, req.linkedin_post, req.offer_id, req.form_url)
    return {"message": "Offer saved successfully"}
