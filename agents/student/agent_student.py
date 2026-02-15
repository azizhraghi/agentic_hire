from .tools.job_scraper import ImprovedJobScraper
from .tools.student_ai import StudentAI
from utils.logger import AgenticLogger
import threading

class AgentStudent:
    """Orchestrateur pour l'étudiant / chercheur d'emploi"""
    
    def __init__(self):
        self.scraper = ImprovedJobScraper()
        self.ai = StudentAI()
        self.logger = AgenticLogger("AgentStudent")
        
    def analyser_profil(self, cv_text: str):
        """Analyse le CV pour en extraire le profil"""
        return self.ai.analyze_cv(cv_text)
        
    def chercher_et_matcher(self, profil_data: dict):
        """
        1. Extrait mots clés
        2. Scrape les jobs
        3. Calcule le matching
        """
        keywords = profil_data.get('technical_skills', [])[:3]
        role = profil_data.get('primary_role')
        if role:
            keywords.insert(0, role)
            
        self.logger.info(f"Recherche pour : {keywords}")
        
        # Scraping
        jobs = self.scraper.scrape_all_sources(keywords, max_jobs=10)
        
        if not jobs:
            return []
            
        # Matching
        matched_jobs = self.ai.match_jobs(profil_data, jobs)
        return matched_jobs
