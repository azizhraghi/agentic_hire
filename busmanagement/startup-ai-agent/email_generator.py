# -*- coding: utf-8 -*-
"""
Email Generator — Génère des emails de prospection personnalisés
avec estimation de probabilité de réponse.
"""
import time
import json
import re
from typing import List, Optional
from google import genai
from models import (
    UserStartupInput, MatchResult, Investor, EmailDraft
)

FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


class EmailGenerator:
    """Génère des emails de prospection et estime la probabilité de réponse."""

    def __init__(self, client: genai.Client, model_name: str = "gemini-2.0-flash"):
        self.client = client
        self.model_name = model_name

    def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Appelle Gemini avec retry et fallback."""
        for model in FALLBACK_MODELS:
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    return response.text
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        time.sleep((attempt + 1) * 2)
                        continue
                    if attempt == max_retries - 1:
                        continue
                    time.sleep(1)
        return ""

    def estimate_response_probability(
        self,
        investor: Investor,
        user_input: UserStartupInput,
        match_context: Optional[List[MatchResult]] = None
    ) -> dict:
        """
        Estime la probabilité de réponse d'un investisseur.
        
        Returns:
            dict avec probability (0-100), priority ('high'/'medium'/'low'),
            best_day, best_time, reasoning
        """
        base_score = 30.0

        # Sector alignment bonus (+20 max)
        user_sector_str = user_input.sector.value
        inv_industries = [ind.value for ind in investor.preferred_industries]
        sector_map = {
            "fintech": ["fintech"],
            "healthtech": ["healthtech", "biotech"],
            "edtech": ["edtech", "saas"],
            "ecommerce": ["ecommerce"],
            "saas": ["saas"],
            "ai_ml": ["saas", "other"],
            "biotech": ["biotech", "healthtech"],
        }
        related = sector_map.get(user_sector_str, [user_sector_str])
        sector_overlap = len(set(related) & set(inv_industries))
        if user_sector_str in inv_industries:
            base_score += 20
        elif sector_overlap > 0:
            base_score += 12

        # Stage alignment bonus (+15 max)
        user_stage_map = {
            "pre_seed": "idée",
            "seed": "mvp",
            "series_a": "early_traction",
            "series_b": "growth",
            "series_c_plus": "scale",
            "growth": "growth",
            "mature": "scale",
        }
        mapped_stage = user_stage_map.get(user_input.stage.value, "mvp")
        inv_stages = [s.value for s in investor.preferred_stages]
        if mapped_stage in inv_stages:
            base_score += 15

        # Investment range fit (+10 max)
        if user_input.revenue > 0:
            needed = user_input.revenue * 2 * 1.05  # Rough estimate of funding needed (converted to USD)
            if investor.investment_range_min <= needed <= investor.investment_range_max:
                base_score += 10
            elif needed <= investor.investment_range_max:
                base_score += 5

        # Recent activity bonus (+10 max)
        if investor.last_investment_date:
            from datetime import date
            days_since = (date.today() - investor.last_investment_date).days
            if days_since < 90:
                base_score += 10
            elif days_since < 180:
                base_score += 5

        # Match context bonus (+5 max)
        if match_context:
            avg_score = sum(m.similarity_score for m in match_context) / len(match_context)
            if avg_score > 70:
                base_score += 5

        # Match score bonus from investor's own match_score (+10 max)
        if investor.match_score:
            base_score += min(10, investor.match_score / 10)

        probability = min(95, max(5, base_score))

        # Determine priority
        if probability >= 65:
            priority = "high"
        elif probability >= 40:
            priority = "medium"
        else:
            priority = "low"

        # Best timing (Tuesday-Thursday, 9-11 AM)
        best_days = ["Mardi", "Mercredi", "Jeudi"]
        best_times = ["09:00", "10:00", "10:30"]

        import random
        random.seed(hash(investor.name))

        return {
            "probability": round(probability, 1),
            "priority": priority,
            "best_day": random.choice(best_days),
            "best_time": random.choice(best_times),
            "reasoning": self._build_reasoning(investor, user_input, probability),
        }

    def _build_reasoning(self, investor: Investor, user_input: UserStartupInput, prob: float) -> str:
        """Construit un raisonnement expliquant la probabilité."""
        parts = []
        if prob >= 60:
            parts.append(f"{investor.name} investit activement dans le secteur {user_input.sector.value}")
        if prob >= 40:
            parts.append(f"Ticket d'investissement compatible avec votre profil")
        if prob < 40:
            parts.append(f"Alignement sectoriel partiel — personnaliser l'approche")
        return ". ".join(parts) + "."

    def generate_outreach_email(
        self,
        user_input: UserStartupInput,
        investor: Investor,
        match_context: Optional[List[MatchResult]] = None,
    ) -> EmailDraft:
        """
        Génère un email de prospection personnalisé pour un investisseur.
        """
        # Get match context summary
        match_summary = ""
        if match_context:
            top_matches = match_context[:3]
            match_names = [m.reference_startup.name for m in top_matches]
            match_summary = f"Startups de référence similaires: {', '.join(match_names)}"

        prompt = f"""Tu es un expert en levée de fonds pour des startups tunisiennes visant l'international (USA/Europe). 
Rédige un email de prospection professionnel et personnalisé en français.

INFORMATIONS SUR LA STARTUP:
- Nom: {user_input.company_name or 'Notre startup'}
- Secteur: {user_input.sector.value.replace('_', ' ').title()}
- Localisation: {user_input.location}, Tunisie
- Employés: {user_input.employees}
- CA: {user_input.revenue:,.0f} € (EUR)
- Description: {user_input.description}
{f'- {match_summary}' if match_summary else ''}

INVESTISSEUR CIBLÉ:
- Nom: {investor.name}
- Type: {investor.type.value.replace('_', ' ').title()}
- Secteurs: {', '.join(i.value for i in investor.preferred_industries)}
- Ticket: {investor.investment_range_min:,.0f} - {investor.investment_range_max:,.0f} $ (USD)
- Portfolio: {', '.join(investor.portfolio_companies[:3])}

Réponds UNIQUEMENT au format JSON suivant (pas de markdown, pas de ```):
{{
    "subject": "Objet de l'email (court, accrocheur)",
    "body": "Corps complet de l'email (professionnel, personnalisé, 150-250 mots)"
}}"""

        response = self._generate_with_retry(prompt)

        # Parse response
        subject = f"Opportunité d'investissement — {user_input.sector.value.title()} en Tunisie"
        body = f"Bonjour,\n\nJe me permets de vous contacter concernant notre startup dans le secteur {user_input.sector.value}..."

        if response:
            try:
                # Clean response
                cleaned = response.strip()
                cleaned = re.sub(r'^```json\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
                data = json.loads(cleaned)
                subject = data.get("subject", subject)
                body = data.get("body", body)
            except (json.JSONDecodeError, KeyError):
                pass

        # Estimate response probability
        prob_data = self.estimate_response_probability(investor, user_input, match_context)

        return EmailDraft(
            investor_name=investor.name,
            investor_email=investor.contact_email,
            subject=subject,
            body=body,
            response_probability=prob_data["probability"],
            best_send_day=prob_data["best_day"],
            best_send_time=prob_data["best_time"],
            priority_level=prob_data["priority"],
            reasoning=prob_data["reasoning"],
        )

    def generate_emails_batch(
        self,
        user_input: UserStartupInput,
        investors: List[Investor],
        match_context: Optional[List[MatchResult]] = None,
        max_emails: int = 5,
    ) -> List[EmailDraft]:
        """
        Génère des emails pour plusieurs investisseurs, triés par priorité.
        """
        emails = []
        for investor in investors[:max_emails]:
            try:
                email = self.generate_outreach_email(user_input, investor, match_context)
                emails.append(email)
            except Exception as e:
                print(f"[EmailGenerator] Erreur pour {investor.name}: {e}")
                continue

        # Sort by response probability (highest first)
        emails.sort(key=lambda e: e.response_probability, reverse=True)
        return emails
