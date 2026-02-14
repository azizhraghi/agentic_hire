import requests
import time
import json
import os
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

class HuggingFaceClient:
    """Client unifié pour les APIs Hugging Face"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("HUGGINGFACE_TOKEN")
        if not self.token:
            raise ValueError("Token Hugging Face requis. Ajoutez-le dans .env")
        
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # URLs des modèles
        self.MODELS = {
            "mistral": "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta",
            # Ou alternativement :
            # "mistral": "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta",  # Alternative
            "llama": "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct",
            "whisper": "https://api-inference.huggingface.co/models/openai/whisper-large-v3",
            "bart": "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def query_text(self, model_key: str, prompt: str, max_tokens: int = 500, temperature: float = 0.2) -> Dict:
        """
        Envoie une requête texte à un modèle Hugging Face
        """
        url = self.MODELS.get(model_key)
        if not url:
            raise ValueError(f"Modèle {model_key} non trouvé")
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 503:
                # Le modèle charge, on attend
                time.sleep(5)
                raise Exception("Model loading, retry...")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur API: {e}")
            return {"error": str(e)}
    
    def query_audio(self, audio_bytes: bytes) -> str:
        """
        Transcrit un fichier audio avec Whisper
        """
        url = self.MODELS["whisper"]
        
        try:
            response = requests.post(url, headers=self.headers, data=audio_bytes, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, dict) and "text" in result:
                return result["text"]
            return str(result)
            
        except Exception as e:
            print(f"Erreur transcription: {e}")
            return ""