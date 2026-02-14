from utils.logger import HackathonLogger
import time
import random

class AgentLinkedInSearch:
    """Agent pour la recherche de stage sur LinkedIn (Étudiant)"""
    
    def __init__(self):
        self.logger = HackathonLogger("AgentSearch")

    def chercher_stage(self, criteres: dict):
        domaine = criteres.get('field_of_study', 'Domaine inconnu')
        niveau = criteres.get('education_level', 'Niveau inconnu')
        
        self.logger.info(f"Scan LinkedIn pour {niveau} en {domaine}...")
        
        # Mock implementation
        offres = [
            {"titre": f"Stage PFE {domaine}", "entreprise": "TechCorp", "lieu": "Paris"},
            {"titre": f"Stage {domaine} Application", "entreprise": "InnovLabs", "lieu": "Lyon"},
            {"titre": f"Internship {domaine} R&D", "entreprise": "GlobalData", "lieu": "Remote"}
        ]
        
        time.sleep(1.5) # Simuler latence réseau
        
        nb_trouve = random.randint(5, 15)
        self.logger.success(f"{nb_trouve} offres pertinentes trouvées sur LinkedIn")
        
        # Afficher le top 3
        for i, off in enumerate(offres, 1):
            print(f"   {i}. {off['titre']} chez {off['entreprise']} ({off['lieu']})")
            
        return offres
