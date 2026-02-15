from utils.logger import AgenticLogger
import time

class AgentEmail:
    """Agent de communication par email"""
    
    def __init__(self):
        self.logger = AgenticLogger("AgentEmail")
        
    def envoyer_invitation(self, email: str, details: dict):
        self.logger.info(f"Envoi email à : {email}")
        
        # Simulation envoi SMTP
        sujet = f"Invitation entretien - {details.get('job_title', 'Candidature')}"
        date_rdv = details.get('date_rdv', 'Date à définir')
        
        message = (
            f"Bonjour {details.get('prenom', 'Candidat')},\n\n"
            f"Nous avons retenu votre profil pour le poste de {details.get('job_title')}.\n"
            f"Nous vous proposons un entretien le **{date_rdv}**.\n\n"
            "Merci de confirmer votre présence."
        )
        
        # Simuler délai réseau
        time.sleep(0.5)
        
        self.logger.success(f"Convocation envoyée à {email} pour le {date_rdv}")
        return True
