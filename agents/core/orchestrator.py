from models.user import User
from models.schemas import UserType
from agents.core.comprehension.agent_comprehension import AgentComprehension
from agents.entrepreneur.agent_entrepreneur import AgentEntrepreneur
from utils.logger import AgenticLogger
import json
import os
from datetime import datetime

class Orchestrator:
    """
    Chef d'orchestre qui dirige les requêtes vers les bons agents
    """
    def __init__(self):
        self.logger = AgenticLogger("Orchestrator")
        self.comprehension = AgentComprehension()
        # Initialisation de l'agent unifié
        self.agent_entrepreneur = AgentEntrepreneur()
        self.current_user = None

    def set_user(self, user: User):
        self.current_user = user

    def handle_request(self, text: str, user_id: str) -> str:
        """Méthode unifiée pour app.py qui retourne une réponse textuelle"""
        self.logger.info(f"Traitement demande User {user_id}: {text}")
        
        # 1. Analyse
        resultat = self.comprehension.process(text)
        type_user = resultat.type_utilisateur
        
        response = ""
        
        if type_user == UserType.ENTREPRENEUR:
            self._flux_entrepreneur(resultat.donnees_extraites)
            response = "J'ai bien compris que vous êtes **recruteur**. J'ai préparé votre espace pour créer un **post LinkedIn** et gérer les candidatures."
            
        elif type_user == UserType.ETUDIANT:
            self._flux_etudiant(resultat.donnees_extraites)
            response = "J'ai bien compris que vous êtes **candidat**. Vous pouvez uploader votre **CV** ou voir les **offres** de stage correspondant à votre profil."
            
        else:
            response = "Je n'ai pas réussi à déterminer si vous cherchez un emploi ou si vous recrutez. Pouvez-vous préciser ?"
            
        return response

    def traiter_demande(self, texte: str):
        # Gardé pour rétro-compatibilité ou usage interne
        return self.handle_request(texte, "cli_user")

    def _flux_entrepreneur(self, data):
        self.logger.info(">>> Lancement du FLUX ENTREPRENEUR (Unifié)")
        
        # Délégation complète à l'AgentEntrepreneur
        try:
            user_id = self.current_user.id if self.current_user else "anonymous"
            artifacts = self.agent_entrepreneur.creer_mission(user_id, data)
            
            # Sauvegarde des résultats
            self._sauvegarder_donnees(data, "entrepreneur", artifacts)
            self.logger.info("Cycle Entrepreneur terminé avec succès.")
            
        except Exception as e:
            self.logger.error(f"Erreur durant le cycle Entrepreneur: {e}")

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
