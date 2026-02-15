# -*- coding: utf-8 -*-
"""
Matching Engine — Algorithme de matching multi-facteurs entre
la startup de l'utilisateur et les startups de référence US.
"""
import math
import time
import json
import re
from typing import List, Optional, Dict
from google import genai
from models import (
    UserStartupInput, ReferenceStartup, MatchResult,
    Sector, GrowthStage
)

# Fallback models
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

# Sector similarity matrix — related sectors get partial scores
SECTOR_SIMILARITY = {
    (Sector.FINTECH, Sector.INSURTECH): 0.7,
    (Sector.FINTECH, Sector.ECOMMERCE): 0.5,
    (Sector.HEALTHTECH, Sector.BIOTECH): 0.7,
    (Sector.EDTECH, Sector.SAAS): 0.5,
    (Sector.SAAS, Sector.AI_ML): 0.6,
    (Sector.CYBERSECURITY, Sector.SAAS): 0.5,
    (Sector.CLEANTECH, Sector.AGRITECH): 0.4,
    (Sector.FOODTECH, Sector.AGRITECH): 0.5,
    (Sector.PROPTECH, Sector.ECOMMERCE): 0.3,
    (Sector.LOGISTICS, Sector.ECOMMERCE): 0.5,
    (Sector.MEDIATECH, Sector.EDTECH): 0.3,
    (Sector.AI_ML, Sector.CYBERSECURITY): 0.5,
    (Sector.AI_ML, Sector.HEALTHTECH): 0.4,
}

# Growth stage proximity (closer stages = higher score)
STAGE_ORDER = {
    GrowthStage.PRE_SEED: 0,
    GrowthStage.SEED: 1,
    GrowthStage.SERIES_A: 2,
    GrowthStage.SERIES_B: 3,
    GrowthStage.SERIES_C_PLUS: 4,
    GrowthStage.GROWTH: 5,
    GrowthStage.MATURE: 6,
}


class StartupMatcher:
    """Moteur de matching multi-facteurs."""

    # Scoring weights
    WEIGHT_SECTOR = 0.40
    WEIGHT_SIZE = 0.20
    WEIGHT_REVENUE = 0.25
    WEIGHT_STAGE = 0.15

    def __init__(self, client: Optional[genai.Client] = None, model_name: str = "gemini-2.0-flash"):
        self.client = client
        self.model_name = model_name

    def _generate_with_retry(self, prompt: str, max_retries: int = 2) -> str:
        """Appelle Gemini avec retry et fallback."""
        if not self.client:
            return ""
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

    def _sector_similarity(self, s1: Sector, s2: Sector) -> float:
        """Calcule la similarité entre deux secteurs."""
        if s1 == s2:
            return 1.0
        # Check both directions in similarity matrix
        score = SECTOR_SIMILARITY.get((s1, s2), None)
        if score is None:
            score = SECTOR_SIMILARITY.get((s2, s1), 0.1)
        return score

    def _size_similarity(self, emp1: int, emp2: int) -> float:
        """Calcule la similarité de taille (employés) sur échelle log."""
        if emp1 == 0 or emp2 == 0:
            return 0.5
        log_ratio = abs(math.log10(max(emp1, 1)) - math.log10(max(emp2, 1)))
        # Score décroît avec la différence logarithmique
        return max(0, 1.0 - log_ratio / 3.0)

    def _revenue_similarity(self, rev1: float, rev2: float) -> float:
        """Calcule la similarité de CA sur échelle log."""
        # Convert EUR to USD approximation (1 EUR ≈ 1.08 USD)
        rev1_usd = rev1 * 1.08 if rev1 > 0 else 1
        rev2_usd = rev2 if rev2 > 0 else 1
        log_ratio = abs(math.log10(max(rev1_usd, 1)) - math.log10(max(rev2_usd, 1)))
        return max(0, 1.0 - log_ratio / 4.0)

    def _stage_similarity(self, stage1: GrowthStage, stage2: GrowthStage) -> float:
        """Calcule la proximité des stades de croissance."""
        order1 = STAGE_ORDER.get(stage1, 1)
        order2 = STAGE_ORDER.get(stage2, 1)
        diff = abs(order1 - order2)
        return max(0, 1.0 - diff / 6.0)

    def compute_similarity(self, user: UserStartupInput, ref: ReferenceStartup) -> dict:
        """
        Calcule le score de similarité multi-facteurs.
        Retourne un dict avec les scores individuels et le score total.
        """
        sector_score = self._sector_similarity(user.sector, ref.sector)
        size_score = self._size_similarity(user.employees, ref.employees)
        revenue_score = self._revenue_similarity(user.revenue, ref.revenue)
        stage_score = self._stage_similarity(user.stage, ref.growth_stage)

        total = (
            sector_score * self.WEIGHT_SECTOR +
            size_score * self.WEIGHT_SIZE +
            revenue_score * self.WEIGHT_REVENUE +
            stage_score * self.WEIGHT_STAGE
        )

        return {
            "total": round(total * 100, 1),
            "sector": round(sector_score * 100, 1),
            "size": round(size_score * 100, 1),
            "revenue": round(revenue_score * 100, 1),
            "stage": round(stage_score * 100, 1),
        }

    def _generate_match_reasons(self, user: UserStartupInput, ref: ReferenceStartup, scores: dict) -> List[str]:
        """Génère des raisons de matching lisibles."""
        reasons = []

        if scores["sector"] >= 80:
            reasons.append(f"Même secteur: {ref.sector.value.replace('_', ' ').title()}")
        elif scores["sector"] >= 50:
            reasons.append(f"Secteurs liés: {user.sector.value} ↔ {ref.sector.value}")

        if scores["size"] >= 70:
            reasons.append(f"Taille comparable: ~{ref.employees} employés")
        
        if scores["revenue"] >= 60:
            reasons.append(f"CA comparable (ajusté): ${ref.revenue:,.0f}")

        if scores["stage"] >= 70:
            reasons.append(f"Même stade: {ref.growth_stage.value.replace('_', ' ').title()}")

        if ref.funding_total and ref.funding_total > 0:
            reasons.append(f"Financement levé: ${ref.funding_total:,.0f}")

        reasons.append(f"Basée à {ref.location}, {ref.state or 'US'}")

        return reasons

    def _generate_match_explanation(self, user: UserStartupInput, ref: ReferenceStartup, score: float) -> str:
        """Utilise Gemini pour générer une explication détaillée du matching."""
        prompt = f"""Tu es un expert en analyse de startups. Explique brièvement (3-4 phrases en français) 
pourquoi cette startup américaine est pertinente comme référence pour un entrepreneur tunisien.

Startup de l'utilisateur:
- Secteur: {user.sector.value}
- Localisation: {user.location}, Tunisie
- Employés: {user.employees}
- CA: {user.revenue} TND
- Description: {user.description}

Startup de référence US:
- Nom: {ref.name}
- Secteur: {ref.sector.value}
- Localisation: {ref.location}, {ref.state}
- Employés: {ref.employees}
- CA: ${ref.revenue:,.0f}
- Stade: {ref.growth_stage.value}
- Score de match: {score}%

Réponds UNIQUEMENT avec l'explication, sans titre ni préambule."""

        result = self._generate_with_retry(prompt)
        return result.strip() if result else f"Matching à {score}% basé sur la similarité sectorielle et la taille d'entreprise."

    def _generate_market_insights(self, user: UserStartupInput, ref: ReferenceStartup, score: float) -> Dict:
        """
        Génère une analyse détaillée (SWOT, Idées) via Gemini.
        Retourne un dictionnaire avec les champs structurés.
        """
        prompt = f"""Tu es un expert en stratégie startup et analyse de marché. 
Agis comme un consultant global qui conseille un entrepreneur tunisien.

Analyse cette startup tunisienne en la comparant non seulement à la référence US identifiée, 
mais à L'ENSEMBLE du marché mondial de ce secteur.

Startup Tunisienne:
- Secteur: {user.sector.value}
- Description: {user.description}
- Stade: {user.stage.value}
- Employés: {user.employees}

Reference US Matchée (pour contexte):
- Nom: {ref.name} ({ref.sector.value})
- Description: {ref.description or 'Non disponible'}

Tâche:
1. Explique brièvement le match (pourquoi cette ref est pertinente).
2. Identifie 3 POINTS FORTS de la startup tunisienne pour gagner son marché local/régional.
3. Identifie 3 POINTS FAIBLES ou RISQUES majeurs.
4. Propose 3 IDÉES INNOVANTES concrètes (fonctionnalités, business model, go-to-market) inspirées des meilleures startups mondiales du secteur pour se démarquer.

Format de réponse attendu (JSON uniquement):
{{
    "explanation": "Texte de l'explication du match...",
    "strengths": ["Point fort 1", "Point fort 2", "Point fort 3"],
    "weaknesses": ["Faiblesse 1", "Faiblesse 2", "Faiblesse 3"],
    "innovative_ideas": ["Idée 1", "Idée 2", "Idée 3"],
    "market_positioning": "Une phrase de positionnement stratégique suggéré"
}}
"""
        try:
            response_text = self._generate_with_retry(prompt)
            # Clean md code blocks if present
            cleaned_text = re.sub(r"```json\s*|\s*```", "", response_text).strip()
            # Handle potential JSON parsing errors by cleaning more if needed
            if not cleaned_text.startswith("{"):
                 match = re.search(r"\{.*\}", response_text, re.DOTALL)
                 if match:
                     cleaned_text = match.group(0)
            
            data = json.loads(cleaned_text)
            return data
        except Exception:
            return {
                "explanation": f"Match à {score}% basé sur le secteur et le stade de développement.",
                "strengths": ["Potentiel de croissance local", "Adéquation au marché naissant", "Agilité"],
                "weaknesses": ["Concurrence internationale", "Accès au capital", "Taille du marché"],
                "innovative_ideas": ["Adapter le modèle aux spécificités locales", "Focus mobile", "Partenariats"],
                "market_positioning": "Niche locale"
            }

    def find_similar_startups(
        self,
        user_input: UserStartupInput,
        reference_startups: List[ReferenceStartup],
        top_k: int = 10,
        generate_explanations: bool = True
    ) -> List[MatchResult]:
        """
        Trouve les top-K startups les plus similaires.
        
        Args:
            user_input: Profil de l'utilisateur
            reference_startups: Liste des startups de référence
            top_k: Nombre de résultats à retourner
            generate_explanations: Si True, génère des explications via Gemini
            
        Returns:
            Liste triée de MatchResult par score décroissant
        """
        results = []

        for ref in reference_startups:
            scores = self.compute_similarity(user_input, ref)
            reasons = self._generate_match_reasons(user_input, ref, scores)

            result = MatchResult(
                reference_startup=ref,
                similarity_score=scores["total"],
                sector_score=scores["sector"],
                size_score=scores["size"],
                revenue_score=scores["revenue"],
                stage_score=scores["stage"],
                match_reasons=reasons,
            )
            results.append(result)

        # Sort by score descending
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        top_results = results[:top_k]

        # Generate Gemini insights only for top results
        if generate_explanations and self.client:
            # We fetch detailed insights for the top 3 matches to save time/tokens, simple expl for others if needed
            for i, result in enumerate(top_results[:5]): 
                insights = self._generate_market_insights(
                    user_input,
                    result.reference_startup,
                    result.similarity_score
                )
                
                # Populate new fields
                top_results[i].match_explanation = insights.get("explanation", "")
                top_results[i].strengths = insights.get("strengths", [])
                top_results[i].weaknesses = insights.get("weaknesses", [])
                top_results[i].innovative_ideas = insights.get("innovative_ideas", [])
                top_results[i].market_positioning = insights.get("market_positioning", "")

        return top_results
