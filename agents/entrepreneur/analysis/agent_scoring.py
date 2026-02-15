from utils.logger import AgenticLogger
import time
import random

class AgentCandidateScoring:
    """Agent d'analyse et de scoring des candidatures"""
    
    def __init__(self):
        self.logger = AgenticLogger("AgentScoring")
        
    def analyser_candidats(self, responses: list):
        self.logger.info(f"Analyse de {len(responses)} candidatures reçues...")
        
        # Simulation du traitement IA
        scores = []
        for cand in responses:
            score = random.randint(60, 95)
            self.logger.info(f"Analyse profil: {cand.get('nom')} -> Score: {score}/100")
            scores.append({**cand, "score": score})
            
        tri_candidats = sorted(scores, key=lambda x: x['score'], reverse=True)
        self.logger.success("Classement final des candidats généré")
        return tri_candidats

class AgentSheetGenerator:
    """Générateur de planning d'entretiens"""
    
    def __init__(self):
        self.logger = AgenticLogger("AgentSheet")
        
    def generer_planning(self, candidats_retenus: list):
        self.logger.info("Génération du fichier Excel pour les entretiens...")
        filename = "planning_entretiens_final.xlsx"
        self.logger.success(f"Fichier exporté: {filename}")
        return filename
