"""
Agent Comprehension - LLM-Powered Intent Detection
===================================================
Uses Mistral/Gemini to truly UNDERSTAND user intent,
with rule-based fallback if LLM is unavailable.
"""

import os
import re
import json
import requests
import logging
from models.schemas import UserType, ComprehensionOutput
from utils.logger import AgenticLogger

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

class AgentComprehension:
    """
    LLM-powered comprehension agent that UNDERSTANDS user intent.
    Falls back to keyword matching only if LLM is unavailable.
    """
    
    def __init__(self):
        self.logger = AgenticLogger("AgentComprehension")
        
        # LLM config - reuse the same keys as the rest of the app
        self.api_key = (
            os.getenv('MISTRAL_API_KEY') 
            or os.getenv('GOOGLE_API_KEY') 
            or os.getenv('HUGGINGFACE_TOKEN')
        )
        self.model = os.getenv('MISTRAL_MODEL', 'mistral-small-latest')
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-lite')
        self.mistral_api_url = "https://api.mistral.ai/v1/chat/completions"
        
        # Determine provider
        if os.getenv('MISTRAL_API_KEY'):
            self.provider = 'mistral'
            self.api_key = os.getenv('MISTRAL_API_KEY')
        elif os.getenv('GOOGLE_API_KEY'):
            self.provider = 'gemini'
            self.api_key = os.getenv('GOOGLE_API_KEY')
        else:
            self.provider = 'none'
    
    # =================================================================
    # LLM CALLING
    # =================================================================
    
    def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """Route to correct LLM provider"""
        try:
            if self.provider == 'mistral':
                return self._call_mistral(prompt, system_prompt)
            elif self.provider == 'gemini':
                return self._call_gemini(prompt, system_prompt)
            else:
                return ""
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return ""
    
    def _call_mistral(self, prompt: str, system_prompt: str = None) -> str:
        """Call Mistral AI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1500
        }
        
        response = requests.post(self.mistral_api_url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _call_gemini(self, prompt: str, system_prompt: str = None) -> str:
        """Call Gemini API with proper error handling"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.api_key}"
        
        # Build the full prompt - combine system + user for Gemini
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        data = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": 0.1, 
                "maxOutputTokens": 1500,
                "responseMimeType": "application/json"
            }
        }
        
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=15)
        
        if response.status_code != 200:
            self.logger.error(f"Gemini HTTP {response.status_code}: {response.text[:200]}")
            return ""
        
        result = response.json()
        
        # Check for prompt feedback / block reasons
        if 'promptFeedback' in result:
            feedback = result['promptFeedback']
            if feedback.get('blockReason'):
                self.logger.error(f"Gemini blocked: {feedback.get('blockReason')}")
                return ""
        
        # Extract text from candidates
        if 'candidates' in result and result['candidates']:
            candidate = result['candidates'][0]
            
            # Check finish reason
            finish_reason = candidate.get('finishReason', '')
            if finish_reason == 'SAFETY':
                self.logger.error("Gemini response blocked by safety filter")
                return ""
            
            if 'content' in candidate and 'parts' in candidate['content']:
                return candidate['content']['parts'][0].get('text', '')
        
        self.logger.error(f"Gemini: No candidates in response: {json.dumps(result)[:300]}")
        return ""
    
    def _parse_json_response(self, text: str) -> dict:
        """Extract JSON from LLM response"""
        if not text:
            return {}
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
        try:
            return json.loads(text)
        except:
            return {}
    
    # =================================================================
    # MAIN PROCESS METHOD
    # =================================================================
    
    def process(self, texte: str) -> ComprehensionOutput:
        """
        Analyze user text using LLM first, fallback to keywords.
        """
        self.logger.info(f"Analyse du texte: {texte[:100]}...")
        
        # Try LLM-based detection first
        if self.api_key:
            result = self._process_with_llm(texte)
            if result:
                return result
            self.logger.warning("LLM detection failed, falling back to keyword matching")
        
        # Fallback to keyword-based detection
        return self._process_with_keywords(texte)
    
    # =================================================================
    # LLM-BASED DETECTION (PRIMARY)
    # =================================================================
    
    def _process_with_llm(self, texte: str) -> ComprehensionOutput:
        """Use LLM to understand user intent and extract data"""
        
        # Single combined prompt (works better with Gemini)
        prompt = f"""You are an intent classifier for a recruitment platform.

Classify this message: "{texte}"

Determine if the user is:
- ENTREPRENEUR: someone who wants to HIRE, recruit, or find candidates for a job
- ETUDIANT: someone LOOKING FOR a job, internship, stage, work, or opportunity

Rules:
- "looking for a job/internship/work" = ETUDIANT
- "want to hire/recruit" = ENTREPRENEUR  
- Handle typos and any language
- Only use AUTRE if truly impossible to determine

Return this JSON:
{{
    "user_type": "ENTREPRENEUR" or "ETUDIANT" or "AUTRE",
    "confidence": 0.0 to 1.0,
    "reasoning": "why",
    "extracted_data": {{}}
}}

For extracted_data, include relevant fields:
- ENTREPRENEUR: job_title, number_needed, skills_required, experience_level, contract_type, location, company_name, salary
- ETUDIANT: education_level, field_of_study, internship_type, duration, skills_required, location
Use "Non spécifié" for unknown fields."""

        try:
            response = self._call_llm(prompt)
            if not response:
                self.logger.error("LLM returned empty response")
                return None
                
            parsed = self._parse_json_response(response)
            if not parsed:
                self.logger.error(f"Failed to parse LLM response: {response[:200]}")
                return None
            
            # Map to UserType
            user_type_str = parsed.get('user_type', 'AUTRE').upper().strip()
            if user_type_str in ('ENTREPRENEUR', 'RECRUITER', 'RECRUTEUR'):
                type_user = UserType.ENTREPRENEUR
            elif user_type_str in ('ETUDIANT', 'CANDIDAT', 'STUDENT', 'CANDIDATE'):
                type_user = UserType.ETUDIANT
            else:
                type_user = UserType.AUTRE
            
            confiance = min(0.95, max(0.3, float(parsed.get('confidence', 0.7))))
            
            # Get extracted data with defaults
            donnees = parsed.get('extracted_data', {})
            if not isinstance(donnees, dict):
                donnees = {}
            if not donnees:
                donnees = {"texte_original": texte[:200]}
            
            # Fill in defaults based on type
            if type_user == UserType.ENTREPRENEUR:
                donnees = self._fill_entrepreneur_defaults(donnees, texte)
            elif type_user == UserType.ETUDIANT:
                donnees = self._fill_etudiant_defaults(donnees, texte)
            
            self.logger.success(
                f"[LLM] Type: {type_user.value} (conf: {confiance:.2f}) "
                f"| {parsed.get('reasoning', 'N/A')}"
            )
            
            return ComprehensionOutput(
                type_utilisateur=type_user,
                confiance=confiance,
                donnees_extraites=donnees,
                texte_original=texte
            )
            
        except Exception as e:
            self.logger.error(f"LLM processing error: {e}")
            return None
    
    def _fill_entrepreneur_defaults(self, donnees: dict, texte: str) -> dict:
        """Ensure entrepreneur data has all required fields"""
        defaults = {
            "job_title": "Non spécifié",
            "number_needed": 1,
            "skills_required": [],
            "experience_level": "Non spécifié",
            "contract_type": "Non spécifié",
            "location": "Non spécifié",
            "company_name": "Non spécifié",
            "duration": "Non spécifié",
            "salary": "Non spécifié",
            "additional_info": texte[:200]
        }
        for key, val in defaults.items():
            if key not in donnees or donnees[key] is None:
                donnees[key] = val
        return donnees
    
    def _fill_etudiant_defaults(self, donnees: dict, texte: str) -> dict:
        """Ensure student data has all required fields"""
        defaults = {
            "education_level": "Non spécifié",
            "field_of_study": "Non spécifié",
            "internship_type": "Stage",
            "duration": "Non spécifié",
            "skills_required": [],
            "location": "Non spécifié",
            "start_date": "Non spécifié",
            "has_cv": "cv" in texte.lower()
        }
        for key, val in defaults.items():
            if key not in donnees or donnees[key] is None:
                donnees[key] = val
        return donnees
    
    # =================================================================
    # KEYWORD-BASED DETECTION (FALLBACK)
    # =================================================================
    
    def _process_with_keywords(self, texte: str) -> ComprehensionOutput:
        """Fallback: rule-based detection when LLM is unavailable"""
        self.logger.info("[Fallback] Using keyword-based detection")
        
        texte_propre = texte.lower()
        mots = set(re.findall(r'\b\w+\b', texte_propre))
        
        mots_entrepreneur = {
            'recruter', 'recrutement', 'embauche', 'embaucher', 'employeur',
            'recrute', 'recrutes', 'recrutons', 'recrutez', 'recrutent',
            'candidat', 'cv', 'profil', 'talent', 'collaborateur',
            'cdi', 'cdd', 'contrat', 'salaire', 'budget',
            'recruit', 'recruiting', 'recruitment', 'hire', 'hiring',
            'employer', 'employee', 'salary', 'company', 'startup',
            'engineer', 'developer', 'position', 'vacancy', 'opening',
            'team', 'needed',
        }
        
        mots_etudiant = {
            'stage', 'stagiaire', 'alternance', 'alternant', 'apprentissage',
            'pfe', 'pfa', 'job', 'internship', 'intern', 'student',
            'étudiant', 'école', 'université', 'formation', 'diplôme',
            'postuler', 'candidature', 'recherche', 'cherche', 'trouver',
            'apply', 'application', 'university', 'school', 'degree',
            'seeking', 'search', 'find', 'opportunity',
        }
        
        phrases_etudiant = [
            'looking for a job', 'looking for an internship', 'looking for work',
            'looking for a stage', 'looking for an opportunity',
            'je cherche un stage', 'je cherche un emploi', 'je cherche du travail',
        ]
        phrases_entrepreneur = [
            'looking for candidates', 'need to hire', 'want to recruit',
            'we are hiring', 'je recrute', 'nous recrutons',
        ]
        
        score_e = len(mots.intersection(mots_entrepreneur))
        score_s = len(mots.intersection(mots_etudiant))
        
        for phrase in phrases_etudiant:
            if phrase in texte_propre:
                score_s += 3
        for phrase in phrases_entrepreneur:
            if phrase in texte_propre:
                score_e += 3
        
        if score_e > score_s and score_e > 0:
            type_user = UserType.ENTREPRENEUR
            confiance = min(0.85, 0.5 + score_e * 0.1)
            donnees = self._fill_entrepreneur_defaults({}, texte)
        elif score_s > 0:
            type_user = UserType.ETUDIANT
            confiance = min(0.85, 0.5 + score_s * 0.1)
            donnees = self._fill_etudiant_defaults({}, texte)
        else:
            type_user = UserType.AUTRE
            confiance = 0.3
            donnees = {"texte_original": texte[:200]}
        
        self.logger.success(f"[Fallback] Type: {type_user.value} (conf: {confiance:.2f})")
        
        return ComprehensionOutput(
            type_utilisateur=type_user,
            confiance=confiance,
            donnees_extraites=donnees,
            texte_original=texte
        )
