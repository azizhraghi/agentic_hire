from utils.logger import HackathonLogger
import time

class AgentGoogleForms:
    """Agent pour la création automatique de formulaires"""
    
    def __init__(self):
        self.logger = HackathonLogger("AgentForms")

    def creer_formulaire(self, details: dict):
        titre = f"Candidature - {details.get('job_title', 'Poste')}"
        self.logger.info(f"Génération du formulaire : {titre}")
        
        sections = [
            "Coordonnées (Nom, Prénom, Email)",
            "CV & Portfolio",
            "Lettre de motivation",
            "Questions spécifiques au poste"
        ]
        
        time.sleep(1) # Simulation réaliste
        
        self.logger.success(f"Formulaire Google Forms créé avec {len(sections)} sections")
        return "https://docs.google.com/forms/d/1XyZ..."
