from google import genai
from datetime import datetime, timedelta
import json
from typing import List, Dict
from models import StartupProfile, LongTermPlan, ProjectPhase

# Fallback models for resilience
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

class PlanningGenerator:
    """Générateur de plans d'affaires à long terme"""
    
    def __init__(self, client: genai.Client, model_name: str):
        self.client = client
        self.model_name = model_name
    
    def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Appelle Gemini avec retry automatique et fallback de modèles"""
        import time
        
        last_error = None
        for model in FALLBACK_MODELS:
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    return response.text
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        wait_time = 2 * (attempt + 1)  # 2s, 4s, 6s
                        print(f"Plan rate limit sur {model}, attente {wait_time}s ({attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        break
            print(f"Plan: passage au modèle suivant après échec sur {model}")
        raise last_error or Exception("Tous les modèles Gemini ont échoué pour le plan")

    def generate_long_term_plan(self, profile: StartupProfile, horizon_months: int = 24) -> LongTermPlan:
        """Génère un plan à long terme pour la startup"""
        
        # Convertir le profil en JSON
        profile_json = profile.model_dump_json(indent=2)
        
        prompt = f"""
Tu es un expert en stratégie de startup, spécialisé dans l'écosystème tunisien. Génère un plan d'affaires détaillé sur {horizon_months} mois.

Profil de la startup:
{profile_json}

Génère un plan structuré en phases avec:

1. Executive Summary (2-3 phrases)
2. Phases détaillées (chaque phase doit avoir):
   - Nom de la phase
   - Durée en mois
   - Objectifs SMART
   - Actions clés (liste détaillée)
   - KPIs à suivre
   - Ressources nécessaires
3. Jalons critiques avec dates (inclure l'obtention du label Startup Act si pertinent)
4. Facteurs de risque (incluant les spécificités du marché tunisien)
5. Besoins financiers par phase (en Dinars Tunisiens - TND)

IMPORTANT: Retourne UNIQUEMENT un JSON valide (sans texte avant ou après) suivant cette structure exacte:
{{
    "executive_summary": "...",
    "phases": [
        {{
            "phase_name": "...",
            "duration_months": 6,
            "objectives": ["...", "..."],
            "key_actions": ["...", "..."],
            "kpis": ["...", "..."],
            "resources_needed": ["...", "..."]
        }}
    ],
    "critical_milestones": [
        {{"date": "Mois X", "milestone": "..."}}
    ],
    "risk_factors": ["...", "..."],
    "funding_requirements_by_phase": {{"Phase 1": 50000, "Phase 2": 150000}}
}}
"""
        
        # Générer le plan via Gemini
        try:
            response_text = self._generate_with_retry(prompt)
        except Exception as e:
            print(f"Erreur Gemini: {e}")
            response_text = ""
        
        # Nettoyer la réponse pour extraire le JSON
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            plan_data = json.loads(response_text.strip())
            
        except Exception as e:
            print(f"Erreur parsing plan: {e}")
            print(f"Réponse brute: {response_text[:500] if response_text else '(vide)'}")
            plan_data = self._generate_default_plan(profile)
        
        # Créer les objets Phase avec des dates
        phases = []
        current_date = datetime.now().date()
        
        for i, phase_data in enumerate(plan_data.get("phases", [])):
            start_date = current_date + timedelta(days=sum(p.duration_months for p in phases) * 30)
            end_date = start_date + timedelta(days=phase_data["duration_months"] * 30)
            
            phase = ProjectPhase(
                phase_name=phase_data["phase_name"],
                duration_months=phase_data["duration_months"],
                start_date=start_date,
                end_date=end_date,
                objectives=phase_data["objectives"],
                key_actions=phase_data["key_actions"],
                kpis=phase_data["kpis"],
                resources_needed=phase_data["resources_needed"]
            )
            phases.append(phase)
        
        # Créer le plan complet
        plan = LongTermPlan(
            startup_name=profile.company_name,
            generated_date=datetime.now(),
            horizon_months=horizon_months,
            executive_summary=plan_data.get("executive_summary", "Plan de développement stratégique"),
            phases=phases,
            critical_milestones=plan_data.get("critical_milestones", []),
            risk_factors=plan_data.get("risk_factors", []),
            funding_requirements_by_phase=plan_data.get("funding_requirements_by_phase", {})
        )
        
        return plan
    
    def _generate_default_plan(self, profile: StartupProfile) -> dict:
        """Génère un plan par défaut adapté au marché tunisien si Gemini échoue"""
        
        return {
            "executive_summary": f"Plan de développement pour {profile.company_name} sur 24 mois dans l'écosystème tunisien",
            "phases": [
                {
                    "phase_name": "Phase 1: Validation et MVP",
                    "duration_months": 6,
                    "objectives": [
                        "Valider le problème auprès de 50 clients potentiels en Tunisie",
                        "Développer un MVP fonctionnel",
                        "Obtenir les 10 premiers clients payants",
                        "Déposer le dossier de labellisation Startup Act"
                    ],
                    "key_actions": [
                        "Conduire 50 entretiens clients",
                        "Développer le produit minimum viable",
                        "Mettre en place un processus de vente initial",
                        "Préparer le dossier Startup Act auprès du Startup Tunisia"
                    ],
                    "kpis": [
                        "Nombre d'entretiens réalisés",
                        "Taux de conversion des essais",
                        "Satisfaction client (NPS)"
                    ],
                    "resources_needed": [
                        "Développeur full-stack",
                        "Outil de CRM",
                        "Budget marketing initial (2K €)"
                    ]
                },
                {
                    "phase_name": "Phase 2: Traction initiale",
                    "duration_months": 6,
                    "objectives": [
                        "Atteindre 50 clients payants",
                        "Atteindre 3K € de MRR",
                        "Optimiser le produit basé sur les retours"
                    ],
                    "key_actions": [
                        "Lancer des campagnes marketing ciblées en Tunisie",
                        "Mettre en place un programme de parrainage",
                        "Améliorer le produit en continu",
                        "Postuler aux programmes d'accélération tunisiens (Flat6Labs, IntilaQ)"
                    ],
                    "kpis": [
                        "MRR (Monthly Recurring Revenue) en €",
                        "CAC (Customer Acquisition Cost)",
                        "LTV (Lifetime Value)"
                    ],
                    "resources_needed": [
                        "Équipe commerciale",
                        "Budget marketing (3K €/mois)",
                        "Support client"
                    ]
                }
            ],
            "critical_milestones": [
                {"date": "Mois 2", "milestone": "Dépôt dossier Startup Act"},
                {"date": "Mois 3", "milestone": "Premières ventes"},
                {"date": "Mois 6", "milestone": "10 clients + Label Startup Act obtenu"},
                {"date": "Mois 12", "milestone": "50 clients"},
                {"date": "Mois 18", "milestone": "Rentabilité"},
                {"date": "Mois 24", "milestone": "Levée de fonds Série A"}
            ],
            "risk_factors": [
                "Concurrence établie sur le marché tunisien",
                "Difficulté d'acquisition client en Tunisie",
                "Besoins en cash plus élevés que prévu"
            ],
            "funding_requirements_by_phase": {
                "Phase 1": 15000,
                "Phase 2": 50000,
                "Phase 3": 100000
            }
        }