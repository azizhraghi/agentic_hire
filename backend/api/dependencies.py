"""
Shared agent dependencies — initialized once at startup.
Provides singleton coordinators via FastAPI's Depends().

All AI API keys come from environment variables ONLY (never from request body).
"""

import os
from functools import lru_cache

from agents.student.multi_agent_system import CVAnalyzerAgent, CoordinatorAgent
from agents.entrepreneur.recruiter_agents import RecruiterCoordinator
from agents.core.orchestrator import Orchestrator


def _get_api_key() -> str:
    """Resolve the AI API key from environment variables only."""
    return os.getenv("MISTRAL_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""


@lru_cache()
def get_cv_analyzer() -> CVAnalyzerAgent:
    return CVAnalyzerAgent(api_key=_get_api_key(), use_mistral=True)


@lru_cache()
def get_student_coordinator() -> CoordinatorAgent:
    return CoordinatorAgent(api_key=_get_api_key(), use_mistral=True)


@lru_cache()
def get_recruiter_coordinator() -> RecruiterCoordinator:
    return RecruiterCoordinator(api_key=_get_api_key(), use_mistral=True)


@lru_cache()
def get_orchestrator() -> Orchestrator:
    return Orchestrator()
