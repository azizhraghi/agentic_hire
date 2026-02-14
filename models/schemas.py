from pydantic import BaseModel
from typing import List, Optional, Literal
from enum import Enum

# Types d'utilisateurs
class UserType(str, Enum):
    ENTREPRENEUR = "ENTREPRENEUR"
    ETUDIANT = "ETUDIANT" 
    AUTRE = "AUTRE"

# Schéma pour recrutement (entrepreneur)
class RecruitmentNeed(BaseModel):
    job_title: str = "Non spécifié"
    number_needed: int = 1
    skills_required: List[str] = []
    experience_level: str = "Non spécifié"
    contract_type: str = "Non spécifié"
    location: str = "Non spécifié"
    company_name: str = "Non spécifié"
    additional_info: str = ""

# Schéma pour stage (étudiant)
class InternshipNeed(BaseModel):
    field: str = "Non spécifié"
    duration_months: int = 6
    skills: List[str] = []
    location: str = "Non spécifié"
    start_date: Optional[str] = None
    has_cv: bool = False

# Schéma principal de compréhension
class ComprehensionOutput(BaseModel):
    type_utilisateur: UserType
    confiance: float
    donnees_extraites: dict
    texte_original: str