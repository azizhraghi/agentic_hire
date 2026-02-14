import json
import os
import hashlib
import uuid
from typing import Optional, List, Dict
from models.user import User, UserRole
from utils.logger import HackathonLogger

class AuthService:
    """Service de gestion de l'authentification (JSON based)"""
    
    def __init__(self, db_path="data/users.json"):
        self.db_path = db_path
        self.logger = HackathonLogger("AuthService")
        self._ensure_db()
        self.current_user: Optional[User] = None

    def _ensure_db(self):
        """Assure que le fichier JSON existe"""
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load_users(self) -> List[dict]:
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_users(self, users: List[dict]):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username, password, role="entrepreneur", email=None) -> Optional[User]:
        """Inscrit un nouvel utilisateur"""
        users = self._load_users()
        
        # Vérifier unicité
        for u in users:
            if u["username"] == username:
                self.logger.warning(f"Tentative d'inscription échouée: {username} existe déjà")
                return None

        new_user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=self._hash_password(password),
            role=role,
            email=email
        )
        
        users.append(new_user.dict())
        self._save_users(users)
        self.logger.success(f"Nouvel utilisateur inscrit: {username} ({role})")
        return new_user

    def login(self, username, password) -> Optional[User]:
        """Connecte un utilisateur"""
        users = self._load_users()
        pwd_hash = self._hash_password(password)
        
        for u_data in users:
            if u_data["username"] == username and u_data["password_hash"] == pwd_hash:
                user = User(**u_data)
                self.current_user = user
                self.logger.success(f"Connexion réussie: {username}")
                return user
        
        self.logger.warning(f"Échec connexion: {username}")
        return None

    def logout(self):
        if self.current_user:
            self.logger.info(f"Déconnexion: {self.current_user.username}")
        self.current_user = None

    def get_current_user_id(self) -> Optional[str]:
        return self.current_user.id if self.current_user else None
