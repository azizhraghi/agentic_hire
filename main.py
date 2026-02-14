import os
import sys
from dotenv import load_dotenv
from utils.hf_client import HuggingFaceClient
from utils.logger import HackathonLogger
from agents.core.orchestrator import Orchestrator
from agents.core.audio.agent_audio import AgentAudio
from services.auth_service import AuthService
from models.schemas import UserType

load_dotenv()

class HackathonPipeline:
    """
    Pipeline principal qui orchestre tous les agents
    """
    
    def __init__(self):
        self.logger = HackathonLogger("Pipeline")
        self.logger.info("Initialisation du pipeline...")
        
        # Initialiser le client Hugging Face
        self.hf_client = HuggingFaceClient()
        
        # Service d'authentification
        self.auth_service = AuthService()
        self.current_user = None
        
        # Initialiser les agents
        self.agent_audio = AgentAudio(self.hf_client)
        self.orchestrator = Orchestrator()
        
        self.logger.success("Pipeline initialisé !")

    def _menu_connexion(self):
        """Gère la boucle de connexion/inscription"""
        while not self.current_user:
            print("\n" + "="*50)
            print("🔐 AUTHENTIFICATION")
            print("="*50)
            print("1. Se connecter")
            print("2. Créer un compte")
            print("3. Quitter")
            
            choix = input("\n> Choix: ").strip()
            
            if choix == "1":
                user = input("Identifiant: ").strip()
                pwd = input("Mot de passe: ").strip()
                self.current_user = self.auth_service.login(user, pwd)
                if not self.current_user:
                    print("❌ Identifiants incorrects.")
            
            elif choix == "2":
                user = input("Nouvel identifiant: ").strip()
                pwd = input("Mot de passe: ").strip()
                role_input = input("Rôle (1=Entrepreneur, 2=Etudiant): ").strip()
                role = "entrepreneur" if role_input == "1" else "etudiant"
                
                self.current_user = self.auth_service.register(user, pwd, role)
                if self.current_user:
                    print(f"✅ Compte créé ! Bienvenue {user}.")
            
            elif choix == "3":
                print("Au revoir ! 👋")
                sys.exit(0)
            
            else:
                print("❌ Option invalide")

        # Configurer l'orchestrateur avec l'utilisateur connecté
        self.orchestrator.set_user(self.current_user)
        print(f"\n👋 Bonjour {self.current_user.username} ({self.current_user.role})")

    def run(self):
        """
        Boucle principale
        """
        # 1. Connexion obligatoire
        self._menu_connexion()

        print("\n" + "="*50)
        print("🤖 AgenticHire - Orchestrateur")
        print("="*50 + "\n")
        
        while True:
            try:
                print("\nOptions:")
                print("1. 📝 Saisir une demande (Texte)")
                print("2. 🎤 Transcrire un fichier audio (Demo)")
                print("3. ❌ Déconnexion / Quitter")
                
                choix = input("\n> Choix: ").strip()
                
                if choix == "1":
                    texte = input("\n📝 Votre demande: ")
                    if texte:
                        self._traiter_texte(texte)
                
                elif choix == "2":
                    chemin = input("\n📁 Chemin du fichier audio: ")
                    self._traiter_audio(chemin)
                    
                elif choix == "3":
                    print("\nDéconnexion...")
                    self.current_user = None
                    self.auth_service.logout()
                    self._menu_connexion() # Retour au menu auth
                
                else:
                    print("\n❌ Option invalide")
            except KeyboardInterrupt:
                print("\nAu revoir ! 👋")
                break
            except Exception as e:
                self.logger.error(f"Erreur inattendue: {e}")

    def _traiter_audio(self, chemin_audio: str):
        self.logger.info("==================================================")
        self.logger.info("TRAITEMENT AUDIO")
        self.logger.info("==================================================")
        
        texte = self.agent_audio.transcrire(chemin_audio)
        
        if texte:
            self.logger.info(f"Texte transcrit: {texte}")
            self._traiter_texte(texte)
        else:
            self.logger.error("Impossible de traiter l'audio")

    def _traiter_texte(self, texte: str):
        self.logger.info("==================================================")
        self.logger.info("TRAITEMENT TEXTE")
        self.logger.info("==================================================")
        
        # Déléguer à l'orchestrateur
        self.orchestrator.traiter_demande(texte)

def main():
    """Point d'entrée principal"""
    pipeline = HackathonPipeline()
    pipeline.run()

if __name__ == "__main__":
    main()