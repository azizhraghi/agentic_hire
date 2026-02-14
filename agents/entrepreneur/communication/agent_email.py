from utils.logger import HackathonLogger
import time

class AgentEmail:
    """Agent de communication par email"""
    
    def __init__(self):
        self.logger = HackathonLogger("AgentEmail")
        
    def envoyer_invitation(self, email: str, details: dict):
        self.logger.info(f"Envoi email à : {email}")
        
        # Simulation envoi SMTP
        sujet = f"Invitation entretien - {details.get('job_title', 'Candidature')}"
        message = f"Bonjour, nous avons retenu votre profil pour le poste de {details.get('job_title')}..."
        
        # Simuler délai réseau
        time.sleep(0.5)
        
        self.logger.success(f"Convocation envoyée avec succès à {email}")
        return True
