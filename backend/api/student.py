"""
Student API Routes
POST /api/student/analyze-cv
POST /api/student/search-jobs
POST /api/student/generate-application
"""

import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

from backend.api.deps import get_current_user
from models.user import User
from agents.student.multi_agent_system import CVAnalyzerAgent, CoordinatorAgent

router = APIRouter(prefix="/api/student", tags=["Student"])


# --- Request / Response Schemas ---

class AnalyzeCVRequest(BaseModel):
    cv_text: str
    api_key: Optional[str] = None

class AnalyzeCVResponse(BaseModel):
    analysis: dict

class SearchJobsRequest(BaseModel):
    cv_text: str
    cv_analysis: Optional[dict] = None
    jobs_per_site: int = 5
    demo_mode: bool = False
    location: str = ""
    include_remote: bool = True
    selected_sources: Optional[List[str]] = None
    api_key: Optional[str] = None

class GenerateApplicationRequest(BaseModel):
    cv_text: str
    job: dict  # { title, company, location, description, ... }
    api_key: Optional[str] = None


# --- Helper ---

def _get_api_key(provided_key: Optional[str] = None) -> str:
    key = provided_key or os.getenv("MISTRAL_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise HTTPException(status_code=400, detail="No AI API key configured.")
    return key


# --- Routes ---

@router.post("/analyze-cv", response_model=AnalyzeCVResponse)
def analyze_cv(req: AnalyzeCVRequest, current_user: User = Depends(get_current_user)):
    """Analyze CV text and extract skills, experience, recommendations."""
    api_key = _get_api_key(req.api_key)

    analyzer = CVAnalyzerAgent(api_key=api_key, use_mistral=True)
    analysis = analyzer.analyze_cv(req.cv_text)

    return AnalyzeCVResponse(analysis=analysis)


@router.post("/search-jobs")
def search_jobs(req: SearchJobsRequest, current_user: User = Depends(get_current_user)):
    """Run intelligent multi-source job search powered by AI agents."""
    api_key = _get_api_key(req.api_key)

    coordinator = CoordinatorAgent(api_key=api_key, use_mistral=True)

    jobs = coordinator.intelligent_job_search(
        cv_text=req.cv_text,
        jobs_per_site=req.jobs_per_site,
        use_demo=req.demo_mode,
        user_location=req.location,
        selected_sources=req.selected_sources,
        include_remote=req.include_remote,
        cached_cv_analysis=req.cv_analysis,
    )

    # Deduplicate
    seen = {}
    for job in jobs:
        key = (job.get("title", "").lower().strip(), job.get("company", "").lower().strip())
        if key not in seen or job.get("ai_match_score", 0) > seen[key].get("ai_match_score", 0):
            seen[key] = job
    unique_jobs = list(seen.values())

    return {"jobs": unique_jobs, "total": len(unique_jobs)}


@router.post("/generate-application")
def generate_application(req: GenerateApplicationRequest, current_user: User = Depends(get_current_user)):
    """Generate optimized CV, cover letter, and LinkedIn message for a specific job."""
    api_key = _get_api_key(req.api_key)

    coordinator = CoordinatorAgent(api_key=api_key, use_mistral=True)
    results = coordinator.run_full_pipeline(req.cv_text, req.job)

    return {
        "optimized_cv": results.get("optimized_cv", ""),
        "cover_letter": results.get("cover_letter", ""),
        "linkedin_message": results.get("linkedin_message", ""),
        "job_analysis": results.get("job_analysis", {}),
    }
