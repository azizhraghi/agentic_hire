from models.user import User
from models.schemas import UserType
from agents.core.comprehension.agent_comprehension import AgentComprehension
from agents.entrepreneur.agent_linkedin_post import AgentLinkedInPost
from agents.entrepreneur.forms.agent_forms import AgentGoogleForms
from utils.logger import HackathonLogger
import json
import os
from datetime import datetime

class Orchestrator:
    """
    Chef d'orchestre qui dirige les requêtes vers les bons agents
    """
    def __init__(self):
        self.logger = HackathonLogger("Orchestrator")
        self.comprehension = AgentComprehension()
        # Initialisation des agents
        self.agent_linkedin = AgentLinkedInPost()
        self.agent_forms = AgentGoogleForms() 
        self.current_user = None

    def set_user(self, user: User):
        self.current_user = user

    def traiter_demande(self, texte: str):
        user_name = self.current_user.username if self.current_user else 'Anon'
        self.logger.info(f"Reçu (User: {user_name}): {texte[:50]}...")
        
        # 1. Comprendre la demande
        resultat = self.comprehension.process(texte)
        type_user = resultat.type_utilisateur
        
        self.logger.info(f"Utilisateur identifié: {type_user}")
        
        # 2. Router selon le type
        if type_user == UserType.ENTREPRENEUR:
            self._flux_entrepreneur(resultat.donnees_extraites)
        elif type_user == UserType.ETUDIANT:
            self._flux_etudiant(resultat.donnees_extraites)
        else:
            self.logger.warning("Type utilisateur inconnu ou non géré.")

    def _flux_entrepreneur(self, data):
        self.logger.info(">>> Lancement du FLUX ENTREPRENEUR")
        
        # 1. Création du Formulaire
        self.logger.info("1. Création du formulaire de candidature...")
        try:
            form_link = self.agent_forms.creer_formulaire(data)
        except Exception as e:
            self.logger.error(f"Erreur Forms: {e}")
            form_link = None
        
        # 2. Publication LinkedIn
        self.logger.info("2. Génération et publication du post LinkedIn...")
        post_info = self.agent_linkedin.poster_offre(data, form_link)
        
        # 3. Sauvegarde (Données + Artefacts)
        artifacts = {
            "form_link": form_link,
            "linkedin_post": post_info.get("content"),
            "linkedin_url": post_info.get("url")
        }
        self._sauvegarder_donnees(data, "entrepreneur", artifacts)
        
        self.logger.info("Cycle Entrepreneur terminé avec succès.")

    def _flux_etudiant(self, data):
        self.logger.info(">>> Lancement du FLUX ETUDIANT")
        self._sauvegarder_donnees(data, "etudiant")
        # Integration point for Student agents (LinkedIn Search)
        print(f"🔍 [Recherche] Scan des offres de stage pour : {data.get('education_level')} en {data.get('field_of_study')}")

    def _sauvegarder_donnees(self, data: dict, type_flux: str, artifacts: dict = None):
        user_id = self.current_user.id if self.current_user else "anonymous"
        # Créer le dossier data s'il n'existe pas
        if not os.path.exists("data"):
            os.makedirs("data")
            
        fichier = f"data/{user_id}_data.json"
        
        # Créer le nouvel enregistrement avec métadonnées
        enregistrement = {
            "id": None, # Sera calculé
            "user_id": user_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type_flux": type_flux,
            "data": data,
            "artifacts": artifacts or {}
        }
        
        try:
            # Charger les données existantes
            historique = []
            if os.path.exists(fichier):
                with open(fichier, "r", encoding="utf-8") as f:
                    contenu = json.load(f)
                    # Gérer l'ancien format (dict simple) et le nouveau (liste)
                    if isinstance(contenu, list):
                        historique = contenu
                    else:
                        historique = [contenu]
            
            # Attribuer un ID incrémental
            enregistrement["id"] = len(historique) + 1
            historique.append(enregistrement)
            
            # Sauvegarder tout l'historique
            with open(fichier, "w", encoding="utf-8") as f:
                json.dump(historique, f, indent=2, ensure_ascii=False)
            self.logger.success(f"Données sauvegardées dans {fichier} (entrée #{enregistrement['id']})")
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde: {e}")
