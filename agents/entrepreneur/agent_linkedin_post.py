from utils.logger import HackathonLogger

class AgentLinkedInPost:
    """Agent responsable de la publication sur LinkedIn"""
    
    def __init__(self):
        self.logger = HackathonLogger("AgentLinkedInPost")

    def poster_offre(self, details: dict):
        job_title = details.get('job_title', 'Poste inconnu')
        self.logger.info(f"Préparation de la publication pour : {job_title}")
        
        # Simulation d'appel API
        self.logger.success(f"Offre '{job_title}' publiée sur LinkedIn (ID: #LI-8923)")
        return "https://www.linkedin.com/jobs/view/3819283"
