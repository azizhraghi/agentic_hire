import json
import os
import streamlit as st
from datetime import datetime
from agents.entrepreneur.agent_linkedin_post import AgentLinkedInPost
from agents.entrepreneur.analysis.agent_scoring import AgentCandidateScoring
from agents.entrepreneur.communication.agent_email import AgentEmail

class AgentEntrepreneur:
    """
    Agent unifié pour l'entrepreneur.
    Gère la création de mission (Post LinkedIn + Lien Formulaire) 
    et le dispatching des candidatures (Scoring + Emailing).
    """

    def __init__(self):
        self.agent_linkedin = AgentLinkedInPost()
        self.agent_scoring = AgentCandidateScoring()
        self.agent_email = AgentEmail()
        
        # URL de base de l'application Streamlit (à configurer selon déploiement)
        self.base_url = "http://localhost:8501"

    def creer_mission(self, user_id: str, data: dict):
        """
        Orchestre la création d'une nouvelle offre d'emploi.
        1. Génère un ID unique pour l'offre.
        2. Génère le lien vers le formulaire Streamlit interne.
        3. Crée le post LinkedIn incluant ce lien.
        4. Retourne les artefacts pour sauvegarde.
        """
        
        # 1. Génération ID Offre (basé sur timestamp court pour la lisibilité)
        offer_id = f"OFF-{int(datetime.now().timestamp())}"
        data['offer_id'] = offer_id
        
        # 2. Lien du formulaire Streamlit
        # L'URL doit pointer vers la page de candidature (gérée dans app.py)
        # On utilise un paramètre de requête pour pré-remplir ou identifier l'offre
        form_link = f"{self.base_url}/?page=candidat&offer_id={offer_id}"
        
        # 3. Génération Post LinkedIn
        # AgentLinkedInPost attend un dictionnaire data et un lien form_link
        post_info = self.agent_linkedin.poster_offre(data, form_link)
        
        # 4. Retourner les résultats pour l'Orchestrator
        artifacts = {
            "offer_id": offer_id,
            "form_link": form_link,
            "linkedin_post": post_info.get("content"),
            "linkedin_url": post_info.get("url")
        }
        
        return artifacts

    def get_candidatures(self, offer_id: str):
        """Retourne la liste brute des candidats pour une offre"""
        return self._lire_candidatures(offer_id)

    def dispatcher_candidatures(self, offer_id: str):
        """
        Récupère les candidatures pour une offre, les score, et envoie les convocs
        avec une date d'entretien planifiée.
        """
        # 1. Lire les candidatures
        candidats = self._lire_candidatures(offer_id)
        
        if not candidats:
            return None

        # 2. Scoring
        candidats_scores = self.agent_scoring.analyser_candidats(candidats)
        
        # 3. Filtrer les meilleurs (ex: Score > 75)
        top_candidats = [c for c in candidats_scores if c.get('score', 0) >= 75]
        
        # 4. Planification & Emailing
        # On commence les entretiens demain à 09h00
        start_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        # Séquence de dates (toutes les heures)
        
        for i, c in enumerate(top_candidats):
            # Calcul du créneau (Index + 1 jour pour éviter le passé si executé tard)
            # Pour faire simple: Demain + i heures
            from datetime import timedelta
            
            slot_time = start_date + timedelta(days=1, hours=i)
            date_str = slot_time.strftime("%d/%m/%Y à %Hh%M")
            
            details = {
                "job_title": c.get("job_title", "Poste"),
                "nom": c.get("nom"), 
                "prenom": c.get("prenom"),
                "date_rdv": date_str
            }
            
            email_candidat = c.get("email")
            if email_candidat:
                self.agent_email.envoyer_invitation(email_candidat, details)
                # On ajoute la date au dict candidat pour l'affichage
                c["date_rdv"] = date_str
        
                c["date_rdv"] = date_str
        
        # 5. Sauvegarder les modifications (dates de rdv) dans le JSON central
        self._sauvegarder_candidatures(offer_id, candidats)
        
        return candidats_scores

    def _sauvegarder_candidatures(self, offer_id: str, candidats_modifies: list):
        """Met à jour les candidatures dans le fichier JSON"""
        file_path = "data/candidatures.json"
        
        if not os.path.exists(file_path):
            return

        try:
            # 1. Lire tout le fichier
            with open(file_path, "r", encoding="utf-8") as f:
                all_apps = json.load(f)
            
            # 2. Mettre à jour les entrées correspondantes
            # On crée un dict par email ou nom pour update facile, ou on remplace tout le bloc
            # Ici on va remplacer les objets de l'offre par ceux modifiés
            
            # On garde ceux qui ne sont PAS de cette offre
            new_apps = [app for app in all_apps if app.get("offer_id") != offer_id]
            
            # On ajoute les modifiés (qui sont tous ceux de cette offre, y compris les non-retenus)
            # Attention: `candidats_modifies` dans dispatcher contient TOUS les candidats de l'offre (scorés)
            new_apps.extend(candidats_modifies)
            
            # 3. Écrire
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(new_apps, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Erreur sauvegarde candidatures: {e}")

    def _lire_candidatures(self, offer_id: str):
        """Lit le fichier JSON central des candidatures"""
        file_path = "data/candidatures.json"
        
        if not os.path.exists("data"):
            os.makedirs("data")
            
        if not os.path.exists(file_path):
            return []
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                all_apps = content if isinstance(content, list) else []
                
                # Filtrer pour l'offre concernée
                result = [app for app in all_apps if app.get("offer_id") == offer_id]
                return result
        except Exception as e:
            print(f"Erreur lecture candidatures: {e}")
            return []
