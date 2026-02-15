from pydantic import BaseModel
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    ENTREPRENEUR = "entrepreneur"
    ETUDIANT = "etudiant"
    ADMIN = "admin"

class User(BaseModel):
    id: str
    username: str
    password_hash: str  # Stocker le hash, jamais le mot de passe clair
    role: Optional[str] = "USER"  # Rôle générique par défaut
    email: Optional[str] = None
    company_name: Optional[str] = None # Pour entrepreneur
    school_name: Optional[str] = None  # Pour étudiant

    class Config:
        use_enum_values = True
