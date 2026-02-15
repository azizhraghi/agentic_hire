# -*- coding: utf-8 -*-
import sys
import os

# Fix Windows console encoding for French characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime
import json

from agent import StartupBusinessAgent
from models import (
    StartupProfile, UserSession, LongTermPlan, Investor,
    UserStartupInput, Sector, GrowthStage
)
from database import SessionLocal, StartupDB

app = FastAPI(title="StartupMatch AI API", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser l'agent (singleton)
agent = StartupBusinessAgent()

# Stockage des sessions en mémoire
sessions = {}

# ═══════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime

class ProfileRequest(BaseModel):
    session_id: str

class AnalyzeRequest(BaseModel):
    description: str

class StartupMatchRequest(BaseModel):
    """Requête pour le pipeline StartupMatch AI complet"""
    sector: str
    location: str
    latitude: float = 36.8065
    longitude: float = 10.1815
    employees: int
    revenue: float = 0
    description: str
    company_name: Optional[str] = None
    stage: str = "seed"
    governorate: Optional[str] = None

# ═══════════════════════════════════════════
# LEGACY ENDPOINTS (backward compat)
# ═══════════════════════════════════════════

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal de conversation"""
    session_id = request.session_id or str(uuid.uuid4())
    result = await agent.process_message(request.message, session_id)
    if session_id not in sessions:
        sessions[session_id] = {
            "session_id": session_id, "messages": [],
            "profile": None, "created_at": datetime.now()
        }
    sessions[session_id]["messages"].append({
        "user": request.message, "assistant": result["response"],
        "timestamp": datetime.now()
    })
    return ChatResponse(
        response=result["response"], session_id=session_id,
        timestamp=datetime.now()
    )

@app.post("/analyze")
async def analyze_startup(request: AnalyzeRequest):
    """Analyse complète legacy (profil + plan + investisseurs)"""
    if not request.description or len(request.description.strip()) < 10:
        raise HTTPException(status_code=400, detail="Description trop courte (min 10 caractères)")
    try:
        result = agent.full_analysis(request.description)
        return {
            "profile": result["profile"].model_dump(),
            "plan": result["plan"].model_dump(),
            "investors": [inv.model_dump() for inv in result["investors"]],
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            raise HTTPException(status_code=429, detail="Limite de quota Gemini atteinte.")
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse: {error_msg}")

# ═══════════════════════════════════════════
# STARTUPMATCH AI ENDPOINTS
# ═══════════════════════════════════════════

@app.post("/startupmatch")
async def startupmatch_full(request: StartupMatchRequest):
    """
    Pipeline complet StartupMatch AI en 7 étapes.
    Retourne: matches, trajectoires, investisseurs, emails, dashboard.
    """
    try:
        # Map string values to enums
        try:
            sector = Sector(request.sector.lower())
        except ValueError:
            sector = Sector.OTHER

        try:
            stage = GrowthStage(request.stage.lower())
        except ValueError:
            stage = GrowthStage.SEED

        user_input = UserStartupInput(
            sector=sector,
            location=request.location,
            governorate=request.governorate,
            latitude=request.latitude,
            longitude=request.longitude,
            employees=request.employees,
            revenue=request.revenue,
            description=request.description,
            company_name=request.company_name,
            stage=stage,
        )

        result = agent.startupmatch_analysis(user_input)

        return {
            "user_input": result["user_input"].model_dump(),
            "matches": [m.model_dump() for m in result["matches"]],
            "trajectories": [t.model_dump() for t in result["trajectories"]],
            "investors": [inv.model_dump() for inv in result["investors"]],
            "emails": [e.model_dump() for e in result["emails"]],
            "dashboard": result["dashboard"].model_dump(),
            "map_data": result["map_data"],
            "execution_time": result["execution_time"],
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            raise HTTPException(status_code=429, detail="Limite de quota Gemini atteinte.")
        raise HTTPException(status_code=500, detail=f"Erreur StartupMatch: {error_msg}")

@app.post("/match")
async def match_startups(request: StartupMatchRequest):
    """Étape 2: Trouve les startups US similaires."""
    try:
        try:
            sector = Sector(request.sector.lower())
        except ValueError:
            sector = Sector.OTHER
        try:
            stage = GrowthStage(request.stage.lower())
        except ValueError:
            stage = GrowthStage.SEED

        user_input = UserStartupInput(
            sector=sector, location=request.location,
            latitude=request.latitude, longitude=request.longitude,
            employees=request.employees, revenue=request.revenue,
            description=request.description, company_name=request.company_name,
            stage=stage,
        )
        reference_startups = agent.dataset_loader.get_reference_startups()
        matches = agent.startup_matcher.find_similar_startups(
            user_input, reference_startups, top_k=10
        )
        return {
            "matches": [m.model_dump() for m in matches],
            "total_reference": len(reference_startups),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur matching: {str(e)}")

@app.post("/trajectory")
async def analyze_trajectory(request: StartupMatchRequest):
    """Étape 4: Analyse les trajectoires des matches."""
    try:
        try:
            sector = Sector(request.sector.lower())
        except ValueError:
            sector = Sector.OTHER
        try:
            stage = GrowthStage(request.stage.lower())
        except ValueError:
            stage = GrowthStage.SEED

        user_input = UserStartupInput(
            sector=sector, location=request.location,
            latitude=request.latitude, longitude=request.longitude,
            employees=request.employees, revenue=request.revenue,
            description=request.description, company_name=request.company_name,
            stage=stage,
        )
        reference_startups = agent.dataset_loader.get_reference_startups()
        matches = agent.startup_matcher.find_similar_startups(
            user_input, reference_startups, top_k=5, generate_explanations=False
        )
        trajectories = agent.analyze_trajectories(matches, user_input)
        return {"trajectories": [t.model_dump() for t in trajectories]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur trajectoire: {str(e)}")

@app.post("/emails")
async def generate_emails(request: StartupMatchRequest):
    """Étape 6: Génère les emails de prospection."""
    try:
        try:
            sector = Sector(request.sector.lower())
        except ValueError:
            sector = Sector.OTHER
        try:
            stage = GrowthStage(request.stage.lower())
        except ValueError:
            stage = GrowthStage.SEED

        user_input = UserStartupInput(
            sector=sector, location=request.location,
            latitude=request.latitude, longitude=request.longitude,
            employees=request.employees, revenue=request.revenue,
            description=request.description, company_name=request.company_name,
            stage=stage,
        )
        # Get investors first
        profile = StartupProfile(
            company_name=user_input.company_name or "Ma Startup",
            industry=agent._map_sector_to_industry(user_input.sector),
            stage=agent._map_growth_to_stage(user_input.stage),
            description=user_input.description, problem_solved="",
            target_market="Marché tunisien", team_size=user_input.employees,
            founders_background="Entrepreneur", location=user_input.location,
        )
        investors = agent.investor_searcher.find_matching_investors(profile)
        emails = agent.email_generator.generate_emails_batch(user_input, investors, max_emails=5)
        return {"emails": [e.model_dump() for e in emails]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur emails: {str(e)}")

# ═══════════════════════════════════════════
# UTILITY ENDPOINTS
# ═══════════════════════════════════════════

@app.post("/generate-plan")
async def generate_plan(request: ProfileRequest):
    """Génère un plan détaillé pour une session"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session_data = sessions[request.session_id]
    conversation = [msg["user"] for msg in session_data["messages"]]
    profile = agent.extract_profile_from_conversation(conversation)
    plan = agent.planning_generator.generate_long_term_plan(profile)
    session_data["profile"] = profile
    session_data["plan"] = plan
    return plan

@app.post("/find-investors")
async def find_investors(request: ProfileRequest):
    """Trouve des investisseurs pour la startup"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session_data = sessions[request.session_id]
    if not session_data.get("profile"):
        conversation = [msg["user"] for msg in session_data["messages"]]
        profile = agent.extract_profile_from_conversation(conversation)
        session_data["profile"] = profile
    else:
        profile = session_data["profile"]
    investors = agent.investor_searcher.find_matching_investors(profile)
    session_data["investors"] = investors
    return investors

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Récupère les données d'une session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session_data = sessions[session_id]
    return {
        "session_id": session_id,
        "created_at": session_data["created_at"],
        "message_count": len(session_data["messages"]),
        "has_profile": session_data["profile"] is not None,
        "has_plan": session_data.get("plan") is not None,
        "has_investors": session_data.get("investors") is not None
    }

@app.get("/dataset/stats")
async def dataset_stats():
    """Retourne les statistiques du dataset de référence."""
    try:
        stats = agent.dataset_loader.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0-startupmatch", "timestamp": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)