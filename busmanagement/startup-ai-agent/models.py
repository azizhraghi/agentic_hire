from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, date
from enum import Enum

class StartupStage(str, Enum):
    IDEA = "idée"
    MVP = "mvp"
    EARLY_TRACTION = "early_traction"
    GROWTH = "growth"
    SCALE = "scale"

class Industry(str, Enum):
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    EDTECH = "edtech"
    BIOTECH = "biotech"
    HARDWARE = "hardware"
    OTHER = "other"

class StartupProfile(BaseModel):
    """Profil de la startup"""
    company_name: str
    industry: Industry
    stage: StartupStage
    description: str
    problem_solved: str
    target_market: str
    team_size: int
    founders_background: str
    current_mrr: Optional[float] = 0
    users_count: Optional[int] = 0
    funding_needed: Optional[float] = None
    location: str
    website: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class ProjectPhase(BaseModel):
    """Phase d'un projet"""
    phase_name: str
    duration_months: int
    start_date: date
    end_date: date
    objectives: List[str]
    key_actions: List[str]
    kpis: List[str]
    resources_needed: List[str]

class LongTermPlan(BaseModel):
    """Plan à long terme complet"""
    startup_name: str
    generated_date: datetime
    horizon_months: int
    executive_summary: str
    phases: List[ProjectPhase]
    critical_milestones: List[Dict[str, str]]
    risk_factors: List[str]
    funding_requirements_by_phase: Dict[str, float]

class InvestorType(str, Enum):
    BUSINESS_ANGEL = "business_angel"
    VC_SEED = "vc_seed"
    VC_SERIES_A = "vc_series_a"
    CORPORATE_VC = "corporate_vc"
    ACCELERATOR = "accelerator"
    GRANT = "grant"

class Investor(BaseModel):
    """Modèle d'investisseur"""
    name: str
    type: InvestorType
    website: str
    description: str
    investment_range_min: float
    investment_range_max: float
    preferred_stages: List[StartupStage]
    preferred_industries: List[Industry]
    portfolio_companies: List[str]
    location: str
    contact_email: Optional[str] = None
    contact_person: Optional[str] = None
    application_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    last_investment_date: Optional[date] = None
    match_score: Optional[float] = None
    reasons_for_match: List[str] = []

class UserSession(BaseModel):
    """Session utilisateur"""
    session_id: str
    profile: StartupProfile
    created_at: datetime
    last_activity: datetime
    generated_plan: Optional[LongTermPlan] = None
    matched_investors: List[Investor] = []


# ═══════════════════════════════════════════════════════════════
# StartupMatch AI — New Models for 7-Step Pipeline
# ═══════════════════════════════════════════════════════════════

class Sector(str, Enum):
    """Secteurs d'activité pour le matching"""
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    EDTECH = "edtech"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    BIOTECH = "biotech"
    AGRITECH = "agritech"
    CLEANTECH = "cleantech"
    PROPTECH = "proptech"
    LOGISTICS = "logistics"
    FOODTECH = "foodtech"
    INSURTECH = "insurtech"
    MEDIATECH = "mediatech"
    CYBERSECURITY = "cybersecurity"
    AI_ML = "ai_ml"
    OTHER = "other"

class GrowthStage(str, Enum):
    """Stade de croissance de la startup"""
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C_PLUS = "series_c_plus"
    GROWTH = "growth"
    MATURE = "mature"

class UserStartupInput(BaseModel):
    """Étape 1: Données saisies par l'utilisateur tunisien"""
    sector: Sector
    location: str = Field(..., description="Ville (ex: Tunis, Paris, New York)")
    governorate: Optional[str] = None
    latitude: float = Field(default=36.8065, description="Latitude de la localisation")
    longitude: float = Field(default=10.1815, description="Longitude de la localisation")
    employees: int = Field(..., ge=1, description="Nombre d'employés")
    revenue: float = Field(default=0, ge=0, description="Chiffre d'affaires annuel en € (EUR)")
    description: str = Field(..., min_length=10, description="Description du projet")
    company_name: Optional[str] = None
    stage: GrowthStage = GrowthStage.SEED
    founded_year: Optional[int] = None

class ReferenceStartup(BaseModel):
    """Startup américaine de référence (enrichie depuis le dataset)"""
    name: str
    sector: Sector
    location: str  # Ville US
    state: Optional[str] = None
    latitude: float
    longitude: float
    employees: int
    revenue: float  # USD annuel
    growth_stage: GrowthStage
    funding_total: Optional[float] = None
    funding_rounds: Optional[List[str]] = []
    description: Optional[str] = None
    founded_year: Optional[int] = None
    key_metrics: Optional[Dict[str, str]] = {}

class MatchResult(BaseModel):
    """Étape 2: Résultat du matching avec une startup de référence"""
    reference_startup: ReferenceStartup
    similarity_score: float = Field(..., ge=0, le=100, description="Score de similarité 0-100")
    sector_score: float = 0
    size_score: float = 0
    revenue_score: float = 0
    stage_score: float = 0
    match_reasons: List[str] = []
    match_explanation: Optional[str] = None
    
    # New fields for Enhanced Matching
    strengths: List[str] = Field(default_factory=list, description="Points forts par rapport au marché")
    weaknesses: List[str] = Field(default_factory=list, description="Points faibles / Risques par rapport au marché")
    innovative_ideas: List[str] = Field(default_factory=list, description="Idées innovantes pour gagner le marché")
    market_positioning: Optional[str] = Field(None, description="Positionnement stratégique suggéré")

class TrajectoryInsight(BaseModel):
    """Étape 4: Analyse de trajectoire d'une startup matchée"""
    startup_name: str
    growth_narrative: str
    key_success_factors: List[str]
    funding_timeline: List[Dict[str, str]]
    tunisian_recommendations: List[str]
    adapted_strategy: str
    risk_warnings: List[str] = []

class EmailDraft(BaseModel):
    """Étape 6: Email de prospection personnalisé"""
    investor_name: str
    investor_email: Optional[str] = None
    subject: str
    body: str
    response_probability: float = Field(..., ge=0, le=100, description="Probabilité de réponse 0-100%")
    best_send_day: str = "Mardi"
    best_send_time: str = "10:00"
    priority_level: str = "medium"  # high, medium, low
    reasoning: str = ""

class DashboardMetrics(BaseModel):
    """Étape 7: Métriques pour le tableau de bord comparatif"""
    user_metrics: Dict[str, float]
    reference_metrics: Dict[str, float]
    comparison_insights: List[str]
    position_summary: str
    growth_gap_analysis: Optional[str] = None
    recommended_kpis: List[str] = []