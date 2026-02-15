import requests
import os
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

class DeepSeekClient:
    """Client pour l'API DeepSeek"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API Key DeepSeek requis. Ajoutez-le dans .env ou passez-le en paramètre")
        
        self.base_url = "https://api.deepseek.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_text(self, prompt: str, max_tokens: int = 800, temperature: float = 0.7) -> str:
        """
        Génère du texte avec DeepSeek
        
        Args:
            prompt: Le prompt à envoyer
            max_tokens: Nombre maximum de tokens à générer
            temperature: Température de génération (0-2, plus élevé = plus créatif)
        
        Returns:
            Le texte généré
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un expert en copywriting RH spécialisé dans la création de posts LinkedIn viraux et engageants."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Extraire le contenu généré
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise Exception("Réponse API invalide")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur API DeepSeek: {e}")
    
    def generate_linkedin_post(self, job_title: str, company: str, location: str, 
                              skills: str, salary: str, form_url: str,
                              experience: str = "Non spécifié", 
                              contract_type: str = "Non spécifié") -> str:
        """
        Génère un post LinkedIn optimisé pour une offre d'emploi
        
        Args:
            job_title: Titre du poste
            company: Nom de l'entreprise
            location: Localisation
            skills: Compétences requises (séparées par des virgules)
            salary: Salaire proposé
            form_url: Lien vers le formulaire de candidature
            experience: Niveau d'expérience requis
            contract_type: Type de contrat
        
        Returns:
            Le post LinkedIn généré
        """
        prompt = f"""Rédige un post LinkedIn VIRAL et professionnel pour recruter un {job_title} chez {company}.

Informations sur l'offre :
- Poste : {job_title}
- Entreprise : {company}
- Localisation : {location}
- Compétences requises : {skills}
- Expérience : {experience}
- Type de contrat : {contract_type}
- Salaire : {salary}
- Lien de candidature : {form_url}

Structure obligatoire du post :
1. 🎣 Une accroche percutante avec un emoji fort (max 2 lignes)
2. 🚀 La mission en une phrase inspirante
3. 🛠️ Les compétences clés sous forme de liste à puces (utilise les compétences fournies)
4. 💎 Pourquoi rejoindre l'entreprise ? (challenge technique, équipe passionnée, impact)
5. 💰 Salaire et avantages
6. 👉 Appel à l'action clair avec le lien de candidature

Ton : Dynamique, professionnel, et engageant. Utilise des emojis de manière intelligente.
Termine avec 3-4 hashtags pertinents pour le poste et la localisation.

IMPORTANT : 
- Sois concret et précis
- Évite les clichés génériques
- Mets en avant ce qui rend cette opportunité unique
- Le post doit donner envie de postuler immédiatement
"""
        
        return self.generate_text(prompt, max_tokens=800, temperature=0.7)
