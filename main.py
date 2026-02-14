import os
import sys
from dotenv import load_dotenv
from utils.hf_client import HuggingFaceClient
from utils.logger import HackathonLogger
from agents.core.orchestrator import Orchestrator
from agents.core.audio.agent_audio import AgentAudio

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
        
        # Initialiser les agents
        # AgentAudio reste ici pour la pré-transcription
        self.agent_audio = AgentAudio(self.hf_client)
        # Orchestrator gère la logique métier
        self.orchestrator = Orchestrator()
        
        self.logger.success("Pipeline initialisé !")

    def run(self):
        """
        Boucle principale
        """
        print("\n" + "="*50)
        print("🤖 AgenticHire - Orchestrateur")
        print("="*50 + "\n")
        
        while True:
            try:
                print("\nOptions:")
                print("1. 📝 Saisir une demande (Texte)")
                print("2. 🎤 Transcrire un fichier audio (Demo)")
                print("3. ❌ Quitter")
                
                choix = input("\n> Choix: ").strip()
                
                if choix == "1":
                    texte = input("\n📝 Votre demande: ")
                    if texte:
                        self._traiter_texte(texte)
                
                elif choix == "2":
                    chemin = input("\n📁 Chemin du fichier audio: ")
                    self._traiter_audio(chemin)
                    
                elif choix == "3":
                    print("\nAu revoir ! 👋")
                    sys.exit(0)
                
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