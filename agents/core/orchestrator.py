from models.user import User
from models.schemas import UserType
from agents.core.comprehension.agent_comprehension import AgentComprehension
from agents.entrepreneur.agent_entrepreneur import AgentEntrepreneur
from utils.logger import AgenticLogger
from services.auth_service import AuthService


class Orchestrator:
    """
    Chef d'orchestre qui dirige les requêtes vers les bons agents.
    Data persistence uses SQLite via AuthService (no more JSON files).
    """

    def __init__(self):
        self.logger = AgenticLogger("Orchestrator")
        self.comprehension = AgentComprehension()
        self.agent_entrepreneur = AgentEntrepreneur()
        self.auth_service = AuthService()
        self.current_user = None

    def set_user(self, user: User):
        self.current_user = user

    def handle_request(self, text: str, user_id: str) -> str:
        """Unified request handler — returns a text response."""
        self.logger.info(f"Traitement demande User {user_id}: {text}")

        # 1. Analyse
        resultat = self.comprehension.process(text)
        type_user = resultat.type_utilisateur

        if type_user == UserType.ENTREPRENEUR:
            self._flux_entrepreneur(resultat.donnees_extraites)
            return (
                "J'ai bien compris que vous êtes **recruteur**. "
                "J'ai préparé votre espace pour créer un **post LinkedIn** et gérer les candidatures."
            )

        elif type_user == UserType.ETUDIANT:
            self._flux_etudiant(resultat.donnees_extraites)
            return (
                "J'ai bien compris que vous êtes **candidat**. "
                "Vous pouvez uploader votre **CV** ou voir les **offres** de stage correspondant à votre profil."
            )

        return "Je n'ai pas réussi à déterminer si vous cherchez un emploi ou si vous recrutez. Pouvez-vous préciser ?"

    def traiter_demande(self, texte: str):
        """Kept for backward compatibility."""
        return self.handle_request(texte, "cli_user")

    def _flux_entrepreneur(self, data):
        self.logger.info(">>> Lancement du FLUX ENTREPRENEUR (Unifié)")
        try:
            user_id = self.current_user.id if self.current_user else "anonymous"
            artifacts = self.agent_entrepreneur.creer_mission(user_id, data)

            # Save to SQLite
            self.auth_service.save_offer(
                user_id=user_id,
                job_data=data,
                linkedin_post=artifacts.get("linkedin_post", ""),
                offer_id=artifacts.get("offer_id", ""),
                form_url=artifacts.get("form_link", ""),
            )
            self.logger.success("Cycle Entrepreneur terminé avec succès.")

        except Exception as e:
            self.logger.error(f"Erreur durant le cycle Entrepreneur: {e}")

    def _flux_etudiant(self, data):
        self.logger.info(">>> Lancement du FLUX ETUDIANT")
        self.logger.info(
            f"Scan des offres de stage pour : {data.get('education_level')} en {data.get('field_of_study')}"
        )
