# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from google import genai
from typing import List, Dict, Any
import json
import time
import re
from datetime import datetime

# Fix Windows console encoding for French characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

from models import (
    StartupProfile, LongTermPlan, Investor,
    UserStartupInput, ReferenceStartup, MatchResult,
    TrajectoryInsight, DashboardMetrics, Sector, GrowthStage
)
from planning_tools import PlanningGenerator
from investor_tools import InvestorSearcher
from dataset_loader import DatasetLoader
from matching_engine import StartupMatcher
from map_generator import MapGenerator
from email_generator import EmailGenerator

load_dotenv()

# Fallback models to try when rate-limited
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

class StartupBusinessAgent:
    """
    Agent principal de conseil en startup (Google Gemini)
    Inclut le pipeline StartupMatch AI en 7 étapes.
    """
    
    def __init__(self, google_api_key: str = None):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not self.google_api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY in .env")
        
        # Initialiser le client Gemini
        self.client = genai.Client(api_key=self.google_api_key)
        self.model_name = "gemini-2.0-flash"
        
        # Outils existants
        self.planning_generator = PlanningGenerator(self.client, self.model_name)
        self.investor_searcher = InvestorSearcher(self.client, self.model_name)
        
        # Nouveaux outils StartupMatch AI
        self.dataset_loader = DatasetLoader(self.client, self.model_name)
        self.startup_matcher = StartupMatcher(self.client, self.model_name)
        self.map_generator = MapGenerator()
        self.email_generator = EmailGenerator(self.client, self.model_name)
        
        # Historique des conversations par session
        self.conversations: Dict[str, List[Dict]] = {}
    
    def _get_system_prompt(self) -> str:
        return """Tu es un expert en conseil de startup et en business management, spécialisé dans l'expansion internationale depuis la Tunisie. 
Ton rôle est d'aider les entrepreneurs tunisiens à structurer leur projet, trouver des financements aux USA et s'internationaliser.

Guidelines:
- Sois précis et concret dans tes recommandations
- Base-toi sur des données et des best practices du marché global (US/Europe)
- Adapte tes conseils au stade spécifique de la startup
- Propose toujours des actions concrètes pour l'export et la levée de fonds internationale
- N'hésite pas à poser des questions pour mieux comprendre le contexte
- Réponds toujours en français, en tenant compte du contexte global (Growth Hacking, Fundraising US, etc.)
- Utilise l'Euro (€) ou le Dollar ($) comme devise de référence (1€ ≈ 1.05$)"""
    
    async def _call_gemini_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Appelle Gemini avec retry automatique et fallback de modèles"""
        last_error = None
        for model in FALLBACK_MODELS:
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=model, contents=prompt
                    )
                    return response.text
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        wait_time = 2 * (attempt + 1)
                        print(f"Rate limit sur {model}, attente {wait_time}s (tentative {attempt+1}/{max_retries})...")
                        await asyncio.sleep(wait_time)
                    else:
                        break
            print(f"Passage au modele suivant apres echec sur {model}")
        raise last_error or Exception("Tous les modeles Gemini ont echoue")
    
    async def process_message(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """Traite un message utilisateur et retourne la réponse"""
        try:
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            history = self.conversations[session_id]
            messages = [self._get_system_prompt()]
            for msg in history[-10:]:
                messages.append(f"{msg['role']}: {msg['content']}")
            messages.append(f"Utilisateur: {message}")
            full_prompt = "\n\n".join(messages)
            reply = await self._call_gemini_with_retry(full_prompt)
            history.append({"role": "Utilisateur", "content": message})
            history.append({"role": "Assistant", "content": reply})
            return {
                "response": reply,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                user_msg = ("Vous avez atteint la limite de quota Gemini. "
                           "Veuillez patienter quelques minutes et réessayer.")
            else:
                user_msg = f"Désolé, une erreur s'est produite: {error_msg}"
            return {"response": user_msg, "error": error_msg, "session_id": session_id}

    def _call_gemini_with_retry_sync(self, prompt: str, max_retries: int = 2) -> str:
        """Appelle Gemini avec retry automatique (version synchrone, retries réduits)"""
        last_error = None
        for model in FALLBACK_MODELS:
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=model, contents=prompt
                    )
                    return response.text
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        wait_time = 2 * (attempt + 1)
                        print(f"Rate limit sur {model}, attente {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        break
            print(f"Passage au modele suivant apres echec sur {model}")
        raise last_error or Exception("Tous les modeles Gemini ont echoue")

    def extract_profile_from_description(self, description: str) -> StartupProfile:
        """Extrait un profil structuré à partir d'une description libre de startup"""
        prompt = f"""
Tu es un expert en analyse de startups. Extrait les informations clés de cette description 
pour créer un profil structuré.

Description fournie par l'utilisateur:
"{description}"

IMPORTANT: Déduis le maximum d'informations de la description. Si une information n'est pas 
explicitement mentionnée, fais une estimation raisonnable basée sur le contexte.

Retourne UNIQUEMENT un JSON valide (sans texte autour) avec ces champs:
{{
    "company_name": "Nom de la startup (ou 'Ma Startup' si non précisé)",
    "industry": "saas|ecommerce|fintech|healthtech|edtech|biotech|hardware|other",
    "stage": "idée|mvp|early_traction|growth|scale",
    "description": "Description résumée de la startup",
    "problem_solved": "Le problème résolu",
    "target_market": "Le marché cible",
    "team_size": 1,
    "founders_background": "Background des fondateurs (estimation si non précisé)",
    "current_mrr": 0,
    "users_count": 0,
    "funding_needed": null,
    "location": "Localisation (estimation si non précisé)",
    "website": null
}}
"""
        try:
            content = self._call_gemini_with_retry_sync(prompt)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            profile_dict = json.loads(content.strip())
            return StartupProfile(**profile_dict)
        except Exception as e:
            print(f"Erreur parsing profil: {e}")
            return StartupProfile(
                company_name="Nouvelle Startup", industry="other", stage="idée",
                description=description[:200], problem_solved="À définir",
                target_market="À définir", team_size=1,
                founders_background="Entrepreneur", location="Tunisie"
            )

    def extract_profile_from_conversation(self, conversation: List[str]) -> StartupProfile:
        """Extrait un profil structuré à partir de la conversation"""
        conversation_text = "\n".join(conversation)
        return self.extract_profile_from_description(conversation_text)

    def full_analysis(self, description: str) -> Dict[str, Any]:
        """
        Analyse complète legacy:
        1. Extrait le profil
        2. Génère plan + investisseurs EN PARALLÈLE
        """
        start_time = time.time()
        print("📋 Extraction du profil startup...")
        profile = self.extract_profile_from_description(description)
        print(f"  ✅ Profil extrait en {time.time() - start_time:.1f}s")
        
        print("📊💰 Génération du plan + recherche d'investisseurs (en parallèle)...")
        parallel_start = time.time()
        with ThreadPoolExecutor(max_workers=2) as executor:
            plan_future = executor.submit(self.planning_generator.generate_long_term_plan, profile)
            investors_future = executor.submit(self.investor_searcher.find_matching_investors, profile)
            plan = plan_future.result()
            investors = investors_future.result()
        print(f"  ✅ Plan + investisseurs en {time.time() - parallel_start:.1f}s")
        print(f"⏱️ Analyse complète en {time.time() - start_time:.1f}s")
        return {"profile": profile, "plan": plan, "investors": investors}

    # ═══════════════════════════════════════════════════════════
    # StartupMatch AI — Pipeline 7 étapes (OPTIMISÉ)
    # ═══════════════════════════════════════════════════════════

    def analyze_trajectories(self, matches: List[MatchResult], user_input: UserStartupInput) -> List[TrajectoryInsight]:
        """Étape 4: Analyse les trajectoires des startups matchées (top 3 seulement)."""
        insights = []
        for match in matches[:3]:  # Réduit de 5 à 3 pour limiter les appels API
            ref = match.reference_startup
            prompt = f"""Tu es un expert en stratégie de startups. Analyse la trajectoire de cette startup américaine
et génère des recommandations pour un entrepreneur tunisien similaire.

STARTUP DE RÉFÉRENCE US:
- Nom: {ref.name}
- Secteur: {ref.sector.value}
- Localisation: {ref.location}, {ref.state}
- Employés: {ref.employees}
- CA: ${ref.revenue:,.0f}
- Stade: {ref.growth_stage.value}
- Financement: ${ref.funding_total or 0:,.0f} levés

STARTUP TUNISIENNE (Ciblant le marché Global/US):
- Secteur: {user_input.sector.value}
- Localisation: {user_input.location}, Tunisie
- Employés: {user_input.employees}
- CA: {user_input.revenue:,.0f} € (EUR)
- Score de matching: {match.similarity_score:.0f}%

Réponds UNIQUEMENT au format JSON (pas de markdown, pas de ```):
{{
    "growth_narrative": "Récit de croissance en 2-3 phrases",
    "key_success_factors": ["facteur 1", "facteur 2", "facteur 3"],
    "funding_timeline": [{{"stage": "Seed", "amount": "$X", "year": "20XX"}}],
    "tunisian_recommendations": ["reco 1 (global expansion)", "reco 2 (US market entry)", "reco 3"],
    "adapted_strategy": "Stratégie adaptée pour une startup tunisienne visant l'international (1-2 phrases)",
    "risk_warnings": ["risque 1", "risque 2"]
}}"""
            try:
                response = self._call_gemini_with_retry_sync(prompt)
                cleaned = response.strip()
                cleaned = re.sub(r'^```json\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
                data = json.loads(cleaned)
                insights.append(TrajectoryInsight(
                    startup_name=ref.name,
                    growth_narrative=data.get("growth_narrative", "Analyse non disponible"),
                    key_success_factors=data.get("key_success_factors", []),
                    funding_timeline=data.get("funding_timeline", []),
                    tunisian_recommendations=data.get("tunisian_recommendations", []),
                    adapted_strategy=data.get("adapted_strategy", ""),
                    risk_warnings=data.get("risk_warnings", []),
                ))
            except Exception as e:
                print(f"[Agent] Erreur trajectoire pour {ref.name}: {e}")
                insights.append(TrajectoryInsight(
                    startup_name=ref.name,
                    growth_narrative=f"{ref.name} est une startup {ref.sector.value} basée à {ref.location}.",
                    key_success_factors=["Innovation sectorielle", "Équipe expérimentée"],
                    funding_timeline=[],
                    tunisian_recommendations=["Adapter le modèle au marché tunisien", "Explorer le Startup Act"],
                    adapted_strategy="Cibler le marché local puis s'étendre à la région MENA.",
                    risk_warnings=["Différences de taille de marché"],
                ))
        return insights

    def generate_dashboard_metrics(self, user_input: UserStartupInput, matches: List[MatchResult]) -> DashboardMetrics:
        """Étape 7: Génère les métriques du tableau de bord comparatif (aucun appel API)."""
        if not matches:
            return DashboardMetrics(
                user_metrics={"employees": user_input.employees, "revenue": user_input.revenue},
                reference_metrics={}, comparison_insights=["Aucun match trouvé"],
                position_summary="Données insuffisantes pour la comparaison.",
            )
        avg_employees = sum(m.reference_startup.employees for m in matches) / len(matches)
        avg_revenue = sum(m.reference_startup.revenue for m in matches) / len(matches)
        avg_funding = sum((m.reference_startup.funding_total or 0) for m in matches) / len(matches)
        avg_score = sum(m.similarity_score for m in matches) / len(matches)

        user_metrics = {
            "employees": float(user_input.employees),
            "revenue_eur": float(user_input.revenue),
            "revenue_usd": float(user_input.revenue * 1.05),  # Approx conversion
        }
        ref_metrics = {
            "avg_employees": round(avg_employees, 0),
            "avg_revenue_usd": round(avg_revenue, 0),
            "avg_funding_usd": round(avg_funding, 0),
            "avg_match_score": round(avg_score, 1),
            "total_matches": float(len(matches)),
        }
        insights = []
        emp_ratio = user_input.employees / max(avg_employees, 1)
        if emp_ratio > 0.8:
            insights.append("✅ Taille d'équipe comparable aux références US")
        elif emp_ratio > 0.3:
            insights.append(f"📈 Équipe {emp_ratio:.0%} de la taille moyenne des références")
        else:
            insights.append(f"⚠️ Équipe plus petite ({user_input.employees} vs {avg_employees:.0f} en moyenne)")

        rev_ratio = (user_input.revenue * 1.05) / max(avg_revenue, 1)
        if rev_ratio > 0.5:
            insights.append("✅ Chiffre d'affaires dans la fourchette des références")
        else:
            insights.append(f"📊 CA à développer ({rev_ratio:.0%} de la moyenne de référence)")
        if avg_score > 70:
            insights.append(f"🎯 Excellent matching moyen: {avg_score:.0f}%")

        position = f"Votre startup à {user_input.location} se positionne "
        if avg_score > 70:
            position += "très favorablement par rapport aux références US."
        elif avg_score > 50:
            position += "correctement avec un potentiel d'amélioration."
        else:
            position += "avec des opportunités de différenciation significatives."

        return DashboardMetrics(
            user_metrics=user_metrics, reference_metrics=ref_metrics,
            comparison_insights=insights, position_summary=position,
            growth_gap_analysis=f"Écart de croissance moyen: {(1 - emp_ratio)*100:.0f}% en taille d'équipe",
            recommended_kpis=["MRR", "Taux de croissance mensuel", "CAC", "LTV", "Burn rate"],
        )

    def startupmatch_analysis(self, user_input: UserStartupInput) -> Dict[str, Any]:
        """
        Pipeline complet StartupMatch AI en 7 étapes.
        OPTIMISÉ: moins d'appels Gemini, plus de parallélisme.
        """
        start_time = time.time()
        results = {}

        # Step 1: Profile
        print("📋 Étape 1/7: Profil utilisateur...")
        results["user_input"] = user_input

        # Step 2: Matching (PAS d'explications Gemini — trop lent)
        print("🔍 Étape 2/7: Recherche de startups similaires...")
        step_start = time.time()
        reference_startups = self.dataset_loader.get_reference_startups()
        matches = self.startup_matcher.find_similar_startups(
            user_input, reference_startups, top_k=10, generate_explanations=False
        )
        results["matches"] = matches
        print(f"  ✅ {len(matches)} matches en {time.time() - step_start:.1f}s")

        # Step 3: Map data
        print("🗺️ Étape 3/7: Carte interactive préparée")
        results["map_data"] = {
            "matches_count": len(matches),
            "user_location": {"lat": user_input.latitude, "lng": user_input.longitude},
        }

        # Steps 4+5+6 ALL in parallel (max 3 trajectories + investors + 3 emails)
        print("📊💰✉️ Étapes 4-6/7: Trajectoires + Investisseurs + Emails (parallèle)...")
        parallel_start = time.time()
        profile = StartupProfile(
            company_name=user_input.company_name or "Ma Startup",
            industry=self._map_sector_to_industry(user_input.sector),
            stage=self._map_growth_to_stage(user_input.stage),
            description=user_input.description, problem_solved="",
            target_market="Marché tunisien", team_size=user_input.employees,
            founders_background="Entrepreneur", location=user_input.location,
        )

        with ThreadPoolExecutor(max_workers=3) as executor:
            traj_future = executor.submit(self.analyze_trajectories, matches, user_input)
            inv_future = executor.submit(self.investor_searcher.find_matching_investors, profile)
            
            # Wait for investors first, then generate emails
            investors = inv_future.result()
            trajectories = traj_future.result()

        results["trajectories"] = trajectories
        results["investors"] = investors
        print(f"  ✅ Trajectoires + investisseurs en {time.time() - parallel_start:.1f}s")

        # Step 6: Emails (réduit à 3 max pour limiter les appels API)
        print("✉️ Étape 6/7: Génération des emails...")
        step_start = time.time()
        emails = self.email_generator.generate_emails_batch(user_input, investors, matches, max_emails=3)
        results["emails"] = emails
        print(f"  ✅ {len(emails)} emails en {time.time() - step_start:.1f}s")

        # Step 7: Dashboard (aucun appel API — calcul local)
        print("📊 Étape 7/7: Tableau de bord comparatif...")
        dashboard = self.generate_dashboard_metrics(user_input, matches)
        results["dashboard"] = dashboard

        total_time = time.time() - start_time
        print(f"⏱️ Pipeline StartupMatch AI complet en {total_time:.1f}s")
        results["execution_time"] = round(total_time, 1)
        return results

    def _map_sector_to_industry(self, sector: Sector) -> str:
        mapping = {
            Sector.FINTECH: "fintech", Sector.HEALTHTECH: "healthtech",
            Sector.EDTECH: "edtech", Sector.ECOMMERCE: "ecommerce",
            Sector.SAAS: "saas", Sector.BIOTECH: "biotech",
            Sector.AI_ML: "saas", Sector.CYBERSECURITY: "saas",
            Sector.INSURTECH: "fintech",
        }
        return mapping.get(sector, "other")

    def _map_growth_to_stage(self, growth: GrowthStage) -> str:
        mapping = {
            GrowthStage.PRE_SEED: "idée", GrowthStage.SEED: "mvp",
            GrowthStage.SERIES_A: "early_traction", GrowthStage.SERIES_B: "growth",
            GrowthStage.SERIES_C_PLUS: "scale", GrowthStage.GROWTH: "growth",
            GrowthStage.MATURE: "scale",
        }
        return mapping.get(growth, "mvp")