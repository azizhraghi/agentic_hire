# -*- coding: utf-8 -*-
from google import genai
import json
import time
from typing import List, Dict
from models import StartupProfile, Investor, InvestorType, StartupStage, Industry

# Fallback models for resilience
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

class InvestorSearcher:
    """Moteur de recherche d'investisseurs tunisiens avec recherche augmentée par IA"""
    
    def __init__(self, client: genai.Client, model_name: str):
        self.client = client
        self.model_name = model_name
        self.investor_database = self._initialize_investor_database()
    
    def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Appelle Gemini avec retry automatique et fallback de modèles"""
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
                        print(f"Investor rate limit sur {model}, attente {wait_time}s ({attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        break
            print(f"Investors: passage au modèle suivant après échec sur {model}")
        raise last_error or Exception("Tous les modèles Gemini ont échoué pour les investisseurs")

    def _initialize_investor_database(self) -> List[Dict]:
        """Base d'investisseurs US / Global pour startups tech"""
        
        return [
            # ═══════════════════════════════════════════
            # 🇺🇸 TOP TIER ACCELERATORS
            # ═══════════════════════════════════════════
            {
                "name": "Y Combinator",
                "type": "accelerator",
                "website": "https://www.ycombinator.com",
                "description": "L'accélérateur le plus prestigieux au monde. Investit $500k dans un grand nombre de startups deux fois par an.",
                "investment_min": 125000,
                "investment_max": 500000,
                "stages": ["idée", "mvp", "early_traction"],
                "industries": ["saas", "fintech", "ecommerce", "edtech", "healthtech", "other"],
                "portfolio": ["Airbnb", "Stripe", "Dropbox", "Coinbase"],
                "location": "San Francisco, CA (Remote friendly)",
                "contact": "apply@ycombinator.com",
                "contact_person": "Admissions Team",
                "linkedin": "https://www.linkedin.com/company/y-combinator/",
                "facebook": "",
                "instagram": ""
            },
            {
                "name": "Techstars",
                "type": "accelerator",
                "website": "https://www.techstars.com",
                "description": "Réseau mondial d'accélérateurs. Investit jusqu'à $120k avec un fort réseau de mentorat.",
                "investment_min": 20000,
                "investment_max": 120000,
                "stages": ["mvp", "early_traction"],
                "industries": ["saas", "fintech", "healthtech", "cleantech", "other"],
                "portfolio": ["SendGrid", "DigitalOcean", "Chainalysis"],
                "location": "Boulder, CO (Global locations)",
                "contact": "apply@techstars.com",
                "contact_person": "Selection Committee",
                "linkedin": "https://www.linkedin.com/company/techstars/",
                "facebook": "",
                "instagram": ""
            },
            {
                "name": "500 Global",
                "type": "accelerator",
                "website": "https://500.co",
                "description": "Fonds de capital-risque et accélérateur early-stage très actif, notamment sur les marchés émergents et internationaux.",
                "investment_min": 150000,
                "investment_max": 500000,
                "stages": ["mvp", "early_traction"],
                "industries": ["saas", "fintech", "ecommerce", "edtech", "other"],
                "portfolio": ["Canva", "Grab", "Credit Karma"],
                "location": "San Francisco, CA (Global)",
                "contact": "submit@500.co",
                "contact_person": "Investment Team",
                "linkedin": "https://www.linkedin.com/company/500-global/",
                "facebook": "",
                "instagram": ""
            },

            # ═══════════════════════════════════════════
            # 🇺🇸 VC SEED / EARLY STAGE (US)
            # ═══════════════════════════════════════════
            {
                "name": "Sequoia Capital (Arc)",
                "type": "vc_seed",
                "website": "https://www.sequoiacap.com/arc/",
                "description": "Programme catalyseur pour les outliers, par l'un des meilleurs fonds VC au monde.",
                "investment_min": 500000,
                "investment_max": 1000000,
                "stages": ["mvp", "early_traction"],
                "industries": ["saas", "fintech", "ai_ml", "crypto", "other"],
                "portfolio": ["Apple", "Google", "WhatsApp"],
                "location": "Menlo Park, CA (US/Europe)",
                "contact": "arc@sequoiacap.com",
                "contact_person": "Arc Team",
                "linkedin": "https://www.linkedin.com/company/sequoia-capital/",
                "facebook": "",
                "instagram": ""
            },
            {
                "name": "Andreessen Horowitz (a16z)",
                "type": "vc_series_a",
                "website": "https://a16z.com",
                "description": "Fonds VC majeur investissant dans la technologie audacieuse. Connu pour son soutien opérationnel massif.",
                "investment_min": 1000000,
                "investment_max": 20000000,
                "stages": ["early_traction", "growth", "scale"],
                "industries": ["saas", "fintech", "crypto", "consumer", "bio", "games"],
                "portfolio": ["Facebook", "Slack", "Lyft"],
                "location": "Menlo Park, CA",
                "contact": "bizplans@a16z.com",
                "contact_person": "General Partners",
                "linkedin": "https://www.linkedin.com/company/andreessen-horowitz/",
                "facebook": "",
                "instagram": ""
            },
            {
                "name": "First Round Capital",
                "type": "vc_seed",
                "website": "https://firstround.com",
                "description": "Le fonds seed le plus réputé, spécialisé dans les premiers chèques institutionnels.",
                "investment_min": 500000,
                "investment_max": 3000000,
                "stages": ["mvp", "early_traction"],
                "industries": ["saas", "fintech", "consumer", "hardware", "healthcare"],
                "portfolio": ["Uber", "Square", "Notion", "Roblox"],
                "location": "San Francisco, CA",
                "contact": "submit@firstround.com",
                "contact_person": "Investment Team",
                "linkedin": "https://www.linkedin.com/company/first-round-capital/",
                "facebook": "",
                "instagram": ""
            },
             {
                "name": "Pear VC",
                "type": "vc_seed",
                "website": "https://pear.vc",
                "description": "Fonds spécialisé early-stage qui s'associe aux fondateurs dès l'idée (Pre-seed/Seed).",
                "investment_min": 250000,
                "investment_max": 2500000,
                "stages": ["idée", "mvp", "early_traction"],
                "industries": ["saas", "fintech", "consumer", "healthtech", "deeptech"],
                "portfolio": ["DoorDash", "Gusto", "Branch"],
                "location": "Palo Alto, CA",
                "contact": "partners@pear.vc",
                "contact_person": "Pear Team",
                "linkedin": "https://www.linkedin.com/company/pearvc/",
                "facebook": "",
                "instagram": ""
            },

            # ═══════════════════════════════════════════
            # 🇺🇸 ANGEL INVESTORS / SYNDICATES
            # ═══════════════════════════════════════════
            {
                "name": "Jason Calacanis (LAUNCH)",
                "type": "business_angel",
                "website": "https://launch.co",
                "description": "Super Angel très actif et hôte du podcast This Week in Startups. Investit via LAUNCH Fund et Syndicate.",
                "investment_min": 25000,
                "investment_max": 500000,
                "stages": ["mvp", "early_traction"],
                "industries": ["saas", "consumer", "marketplaces"],
                "portfolio": ["Uber", "Robinhood", "Calm"],
                "location": "San Francisco, CA",
                "contact": "jason@calacanis.com",
                "contact_person": "Jason Calacanis",
                "linkedin": "https://www.linkedin.com/in/jasoncalacanis/",
                "facebook": "",
                "instagram": ""
            },
            {
                "name": "Naval Ravikant (AngelList)",
                "type": "business_angel",
                "website": "https://nav.al",
                "description": "Fondateur d'AngelList et investisseur légendaire. Cherche des fondateurs exceptionnels.",
                "investment_min": 50000,
                "investment_max": 500000,
                "stages": ["mvp", "early_traction"],
                "industries": ["crypto", "saas", "deeptech"],
                "portfolio": ["Twitter", "Uber", "Notion"],
                "location": "San Francisco, CA",
                "contact": "Via AngelList",
                "contact_person": "Naval Ravikant",
                "linkedin": "https://www.linkedin.com/in/navalr/",
                "facebook": "",
                "instagram": ""
            },
        ]
    
    def _search_local_database(self, profile: StartupProfile) -> List[Dict]:
        """Filtre la base locale d'investisseurs"""
        
        exact_matches = []
        partial_matches = []
        
        for inv in self.investor_database:
            industry_match = profile.industry.value in inv["industries"] or "other" in inv["industries"]
            stage_match = profile.stage.value in inv["stages"]
            
            if industry_match and stage_match:
                exact_matches.append(inv)
            elif industry_match or stage_match:
                partial_matches.append(inv)
        
        # Retourner les matchs exacts en priorité, puis les partiels
        results = exact_matches + partial_matches
        
        # Si toujours pas assez, ajouter le reste
        if len(results) < 5:
            remaining = [inv for inv in self.investor_database if inv not in results]
            results.extend(remaining)
        
        return results[:15]
    
    def _augment_with_gemini(self, profile: StartupProfile, existing_count: int) -> List[Dict]:
        """Utilise Gemini pour suggérer des investisseurs US supplémentaires"""
        
        if existing_count >= 8:
            return []
        
        prompt = f"""Tu es un expert en Venture Capital aux USA (Silicon Valley, NY, etc.). Suggère 5 investisseurs RÉELS 
(VCs, Micro-VCs, Angels, Accelerators) aux ÉTATS-UNIS qui seraient pertinents pour cette startup:

- Secteur: {profile.industry.value}
- Stade: {profile.stage.value}  
- Description: {profile.description}
- Marché cible: {profile.target_market}
- Localisation: {profile.location} (mais cherche financement US)
- Besoin de financement: {profile.funding_needed or 'Non précisé'} € (EUR)

IMPORTANT: 
- Ne propose QUE des investisseurs RÉELS et actifs aux USA qui investissent dans des fondateurs internationaux ou remote.
- Inclus des firmes connues (ex: Pre-seed funds, sector-specific VCs).
- Les montants doivent être en Euro (€) ou USD ($) converti approximativement en €.

Retourne UNIQUEMENT un JSON valide (array) sans texte autour:
[
    {{
        "name": "Nom de l'investisseur",
        "type": "business_angel|vc_seed|vc_series_a|corporate_vc|accelerator|grant",
        "website": "https://...",
        "description": "Description courte et focus d'investissement",
        "investment_min": 100000,
        "investment_max": 1000000,
        "stages": ["mvp", "early_traction"],
        "industries": ["saas", "fintech"],
        "portfolio": ["Startup1", "Startup2"],
        "location": "City, State (USA)",
        "contact": "email ou URL",
        "ai_suggested": true,
        "reason": "Pourquoi cet investisseur US est pertinent"
    }}
]"""
        
        try:
            response_text = self._generate_with_retry(prompt)
            
            # Nettoyer le JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            suggestions = json.loads(response_text.strip())
            
            # Valider les types
            valid_types = {"business_angel", "vc_seed", "vc_series_a", "corporate_vc", "accelerator", "grant"}
            validated = []
            for s in suggestions:
                if s.get("type") in valid_types:
                    s["ai_suggested"] = True
                    validated.append(s)
            
            return validated[:5]
            
        except Exception as e:
            print(f"Gemini augmentation error: {e}")
            return []
    
    def _calculate_match_score(self, investor: Dict, profile: StartupProfile) -> float:
        """Calcule un score de matching entre l'investisseur et la startup"""
        
        scores = []
        
        # Matching industrie (poids 0.3)
        if profile.industry.value in investor.get("industries", []):
            scores.append(1.0)
        else:
            scores.append(0.3)
        
        # Matching stage (poids 0.3)
        if profile.stage.value in investor.get("stages", []):
            scores.append(1.0)
        else:
            stage_order = ["idée", "mvp", "early_traction", "growth", "scale"]
            try:
                inv_stage_idx = min(stage_order.index(s) for s in investor["stages"] if s in stage_order)
                profile_idx = stage_order.index(profile.stage.value)
                distance = abs(inv_stage_idx - profile_idx)
                score = max(0, 1 - (distance * 0.2))
                scores.append(score)
            except Exception:
                scores.append(0.5)
        
        # Matching budget (poids 0.2)
        if profile.funding_needed:
            inv_min = investor.get("investment_min", 0)
            inv_max = investor.get("investment_max", 0)
            if inv_min <= profile.funding_needed <= inv_max:
                scores.append(1.0)
            elif profile.funding_needed < inv_min:
                scores.append(0.4)
            else:
                scores.append(0.6)
        else:
            scores.append(0.7)
        
        # Location — priorité Tunisie (poids 0.1)
        inv_location = investor.get("location", "").lower()
        prof_location = profile.location.lower()
        if "tunis" in inv_location:
            scores.append(1.0)
        elif "afrique" in inv_location or "mena" in inv_location:
            scores.append(0.8)
        elif prof_location in inv_location:
            scores.append(0.7)
        else:
            scores.append(0.5)
        
        # Diversité de portfolio (poids 0.1)
        portfolio = investor.get("portfolio", [])
        portfolio_size = len(portfolio)
        if portfolio_size > 50:
            scores.append(1.0)
        elif portfolio_size > 10:
            scores.append(0.9)
        elif portfolio_size > 3:
            scores.append(0.8)
        else:
            scores.append(0.7)
        
        weights = [0.3, 0.3, 0.2, 0.1, 0.1]
        final_score = sum(s * w for s, w in zip(scores, weights))
        
        return round(final_score * 100, 1)
    
    def _generate_match_reasons(self, investor: Dict, profile: StartupProfile) -> List[str]:
        """Génère des raisons expliquant pourquoi cet investisseur est pertinent"""
        
        reasons = []
        
        if profile.industry.value in investor.get("industries", []):
            reasons.append(f"Investit activement dans votre secteur ({profile.industry.value})")
        
        if profile.stage.value in investor.get("stages", []):
            reasons.append(f"Cible précisément votre stade ({profile.stage.value})")
        
        if profile.funding_needed:
            inv_min = investor.get("investment_min", 0)
            inv_max = investor.get("investment_max", 0)
            if inv_min <= profile.funding_needed <= inv_max:
                reasons.append(f"Ticket d'investissement adapté à vos besoins ({profile.funding_needed:,.0f} €)")
        
        inv_location = investor.get("location", "").lower()
        if "tunis" in inv_location:
            reasons.append("Investisseur basé en Tunisie 🇹🇳")
        elif "afrique" in inv_location:
            reasons.append("Investisseur actif en Afrique du Nord")
        
        if investor.get("ai_suggested"):
            reason = investor.get("reason", "Recommandé par l'IA pour la pertinence sectorielle en Tunisie")
            reasons.append(f"💡 {reason}")
        
        # Ajouter les sociétés du portfolio comme preuve
        portfolio = investor.get("portfolio", [])
        if len(portfolio) > 0 and len(portfolio) <= 5:
            reasons.append(f"Portfolio: {', '.join(portfolio[:3])}")
        
        return reasons[:4]
    
    def find_matching_investors(self, profile: StartupProfile, max_results: int = 10) -> List[Investor]:
        """Trouve les investisseurs tunisiens correspondant au profil (base locale + augmentation Gemini)"""
        
        # 1. Chercher dans la base locale
        local_results = self._search_local_database(profile)
        
        # 2. Augmenter avec Gemini si pas assez de résultats exacts
        gemini_results = self._augment_with_gemini(profile, len(local_results))
        
        # 3. Combiner et scorer
        all_investors = local_results + gemini_results
        matched_investors = []
        seen_names = set()
        
        for inv_data in all_investors:
            name = inv_data.get("name", "")
            if name in seen_names:
                continue
            seen_names.add(name)
            
            score = self._calculate_match_score(inv_data, profile)
            reasons = self._generate_match_reasons(inv_data, profile)
            
            # Filtrer les industries valides
            valid_industries = [i for i in inv_data.get("industries", []) if i in [e.value for e in Industry]]
            valid_stages = [s for s in inv_data.get("stages", []) if s in [e.value for e in StartupStage]]
            
            # Valider le type
            inv_type = inv_data.get("type", "business_angel")
            try:
                investor_type = InvestorType(inv_type)
            except ValueError:
                investor_type = InvestorType.BUSINESS_ANGEL
            
            investor = Investor(
                name=name,
                type=investor_type,
                website=inv_data.get("website", ""),
                description=inv_data.get("description", ""),
                investment_range_min=inv_data.get("investment_min", 0),
                investment_range_max=inv_data.get("investment_max", 0),
                preferred_stages=[StartupStage(s) for s in valid_stages],
                preferred_industries=[Industry(i) for i in valid_industries],
                portfolio_companies=inv_data.get("portfolio", []),
                location=inv_data.get("location", ""),
                contact_email=inv_data.get("contact"),
                match_score=score,
                reasons_for_match=reasons
            )
            
            matched_investors.append(investor)
        
        # Trier par score décroissant
        matched_investors.sort(key=lambda x: x.match_score or 0, reverse=True)
        
        return matched_investors[:max_results]