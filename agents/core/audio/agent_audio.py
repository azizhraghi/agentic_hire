import os
from utils.hf_client import HuggingFaceClient
from utils.logger import HackathonLogger

class AgentAudio:
    """
    Agent pour la transcription audio -> texte
    """
    
    def __init__(self, hf_client: HuggingFaceClient):
        self.hf = hf_client
        self.logger = HackathonLogger("AgentAudio")
    
    def transcrire(self, audio_path: str) -> str:
        """
        Transcrit un fichier audio en texte
        """
        self.logger.info(f"Transcription de: {audio_path}")
        
        if not os.path.exists(audio_path):
            self.logger.error(f"Fichier non trouvé: {audio_path}")
            return ""
        
        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            
            texte = self.hf.query_audio(audio_bytes)
            
            if texte:
                self.logger.success(f"Transcription: {texte[:100]}...")
            else:
                self.logger.warning("Transcription vide")
            
            return texte
            
        except Exception as e:
            self.logger.error(f"Erreur transcription: {e}")
            return ""
    
    def transcrire_depuis_bytes(self, audio_bytes: bytes) -> str:
        """
        Transcrit depuis des bytes audio (pour upload direct)
        """
        return self.hf.query_audio(audio_bytes)