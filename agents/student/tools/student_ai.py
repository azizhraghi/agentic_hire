import json
import logging
import os
import re
from typing import Dict, List, Optional
from utils.deepseek_client import DeepSeekClient
from utils.logger import AgenticLogger

class StudentAI:
    """Consolidates CV Analysis and Matching using DeepSeek"""
    
    def __init__(self):
        self.client = DeepSeekClient()
        self.logger = AgenticLogger("StudentAI")

    def _clean_json(self, text: str) -> str:
        """Nettoie le texte pour extraire le JSON"""
        # Enlever les balises de code
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```', '', text)
        return text.strip()

    def analyze_cv(self, cv_text: str) -> Dict:
        """Analyze CV content to extract skills and profile"""
        self.logger.info("Analyse du CV en cours...")
        
        prompt = f"""
        Tu es un expert en recrutement. Analyse ce CV et extrais les informations clés en JSON.
        
        CV TEXT:
        {cv_text[:3000]}
        
        FORMAT ATTENDU (JSON):
        {{
          "profile_type": "internship/junior/mid/senior",
          "primary_role": "ex: Data Scientist",
          "technical_skills": ["list", "of", "skills"],
          "soft_skills": ["list", "of", "skills"],
          "recommended_roles": ["role1", "role2"],
          "location_preferences": ["ville1", "remote"]
        }}
        """
        
        try:
            response = self.client.generate(prompt)
            if not response:
                return {}
            
            cleaned = self._clean_json(response)
            data = json.loads(cleaned)
            self.logger.success("Analyse CV terminée")
            return data
        except Exception as e:
            self.logger.error(f"Erreur analyse CV: {e}")
            return {}

    def match_jobs(self, cv_analysis: Dict, jobs: List[Dict]) -> List[Dict]:
        """Match CV profile with scraped jobs"""
        self.logger.info(f"Matching de {len(jobs)} offres...")
        
        results = []
        # On fait un matching simple par mots-clés pour économiser les tokens API, 
        # ou un matching LLM par lot si peu d'offres.
        
        # Méthode hybride : Scoring simple d'abord
        cv_skills = set([s.lower() for s in cv_analysis.get('technical_skills', [])])
        cv_role = cv_analysis.get('primary_role', '').lower()
        
        for job in jobs:
            score = 0
            job_title = job.get('title', '').lower()
            job_desc = job.get('description', '').lower()
            
            # Match Titre
            if cv_role in job_title:
                score += 30
                
            # Match Skills
            matches = 0
            for skill in cv_skills:
                if skill in job_desc:
                    matches += 1
            
            # Normalisation score skills (max 50 pts)
            if cv_skills:
                skill_score = min(50, (matches / len(cv_skills)) * 100)
                score += skill_score
            
            job['match_score'] = int(score)
            results.append(job)
            
        # Tri par score
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results
