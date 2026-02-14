from agents.core.comprehension.agent_comprehension import AgentComprehension
from agents.core.audio.agent_audio import AgentAudio
from models.schemas import UserType
from utils.logger import HackathonLogger

class Orchestrator:
    """
    Chef d'orchestre qui dirige les requêtes vers les bons agents
    """
    def __init__(self):
        self.logger = HackathonLogger("Orchestrator")
        self.comprehension = AgentComprehension()
        # Audio sera initialisé si besoin ou passé en paramètre
        # self.audio = AgentAudio(...) 

    def traiter_demande(self, texte: str):
        self.logger.info(f"Reçu: {texte[:50]}...")
        
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
        self._sauvegarder_donnees(data, "entrepreneur")
        # Integration point for Entrepreneur agents (LinkedIn, Forms)
        print(f"✅ [LinkedIn] Offre publiée : {data.get('job_title')}")
        print(f"✅ [Forms] Formulaire candidat généré et prêt.")

    def _flux_etudiant(self, data):
        self.logger.info(">>> Lancement du FLUX ETUDIANT")
        self._sauvegarder_donnees(data, "etudiant")
        # Integration point for Student agents (LinkedIn Search)
        print(f"🔍 [Recherche] Scan des offres de stage pour : {data.get('education_level')} en {data.get('field_of_study')}")

    def _sauvegarder_donnees(self, data: dict, type_flux: str):
        import json
        import os
        from datetime import datetime
        fichier = "extraction_results.json"
        
        # Créer le nouvel enregistrement avec métadonnées
        enregistrement = {
            "id": None,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type_flux": type_flux,
            "data": data
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
