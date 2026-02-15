# -*- coding: utf-8 -*-
"""
Dataset Loader — Charge le dataset HuggingFace et enrichit les données
en startups américaines synthétiques via Gemini AI.
"""
import os
import re
import json
import time
import random
from typing import List, Dict, Optional
from dotenv import load_dotenv
from google import genai
from models import ReferenceStartup, Sector, GrowthStage

load_dotenv()

CACHE_FILE = os.path.join(os.path.dirname(__file__), "startup_reference_data.json")

# Fallback models
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

# US tech hub coordinates for distributing startups
US_TECH_HUBS = [
    {"city": "San Francisco", "state": "CA", "lat": 37.7749, "lng": -122.4194},
    {"city": "San Jose", "state": "CA", "lat": 37.3382, "lng": -121.8863},
    {"city": "Palo Alto", "state": "CA", "lat": 37.4419, "lng": -122.1430},
    {"city": "Mountain View", "state": "CA", "lat": 37.3861, "lng": -122.0839},
    {"city": "New York", "state": "NY", "lat": 40.7128, "lng": -74.0060},
    {"city": "Brooklyn", "state": "NY", "lat": 40.6782, "lng": -73.9442},
    {"city": "Boston", "state": "MA", "lat": 42.3601, "lng": -71.0589},
    {"city": "Cambridge", "state": "MA", "lat": 42.3736, "lng": -71.1097},
    {"city": "Austin", "state": "TX", "lat": 30.2672, "lng": -97.7431},
    {"city": "Seattle", "state": "WA", "lat": 47.6062, "lng": -122.3321},
    {"city": "Denver", "state": "CO", "lat": 39.7392, "lng": -104.9903},
    {"city": "Miami", "state": "FL", "lat": 25.7617, "lng": -80.1918},
    {"city": "Chicago", "state": "IL", "lat": 41.8781, "lng": -87.6298},
    {"city": "Los Angeles", "state": "CA", "lat": 34.0522, "lng": -118.2437},
    {"city": "Portland", "state": "OR", "lat": 45.5152, "lng": -122.6784},
    {"city": "Atlanta", "state": "GA", "lat": 33.7490, "lng": -84.3880},
    {"city": "Raleigh", "state": "NC", "lat": 35.7796, "lng": -78.6382},
    {"city": "Salt Lake City", "state": "UT", "lat": 40.7608, "lng": -111.8910},
    {"city": "Philadelphia", "state": "PA", "lat": 39.9526, "lng": -75.1652},
    {"city": "Washington DC", "state": "DC", "lat": 38.9072, "lng": -77.0369},
]

# Startup name prefixes/suffixes for generation
STARTUP_PREFIXES = [
    "Neo", "Apex", "Flux", "Sync", "Velo", "Quant", "Pixel", "Bloom",
    "Dash", "Orbit", "Pulse", "Wave", "Forge", "Bolt", "Nova", "Rise",
    "Edge", "Core", "Hive", "Torch", "Prism", "Atlas", "Nimbus", "Zeal",
    "Ember", "Nexus", "Spark", "Crest", "Aura", "Helix",
]
STARTUP_SUFFIXES = [
    "Labs", "AI", "Tech", "io", "ly", "Hub", "Sys", "Data",
    "Works", "Logic", "Cloud", "Pay", "Health", "Ed", "Flow",
    "Sense", "Link", "Net", "Stack", "Box", "Ware", "Base",
]

SECTOR_NAMES = {
    Sector.FINTECH: ["Pay", "Capital", "Finance", "Money", "Bank", "Wallet"],
    Sector.HEALTHTECH: ["Health", "Med", "Care", "Vita", "Bio", "Cure"],
    Sector.EDTECH: ["Learn", "Edu", "Skill", "Course", "Academy", "Scholar"],
    Sector.ECOMMERCE: ["Shop", "Cart", "Market", "Store", "Buy", "Trade"],
    Sector.SAAS: ["Cloud", "Dash", "Manage", "Suite", "Platform", "Ops"],
    Sector.BIOTECH: ["Gene", "Cell", "Bio", "Pharma", "Molecule", "Lab"],
    Sector.AGRITECH: ["Farm", "Agro", "Crop", "Soil", "Green", "Harvest"],
    Sector.CLEANTECH: ["Solar", "Wind", "Eco", "Carbon", "Clean", "Energy"],
    Sector.PROPTECH: ["Home", "Prop", "Realty", "Space", "Build", "Nest"],
    Sector.LOGISTICS: ["Ship", "Route", "Fleet", "Cargo", "Move", "Track"],
    Sector.FOODTECH: ["Food", "Meal", "Kitchen", "Chef", "Taste", "Bite"],
    Sector.INSURTECH: ["Cover", "Shield", "Guard", "Policy", "Insure", "Risk"],
    Sector.MEDIATECH: ["Media", "Stream", "Cast", "Studio", "View", "Play"],
    Sector.CYBERSECURITY: ["Shield", "Guard", "Cyber", "Vault", "Lock", "Safe"],
    Sector.AI_ML: ["Neural", "Mind", "Cortex", "Tensor", "Deep", "Algo"],
    Sector.OTHER: ["Innov", "Venture", "Digital", "Smart", "Next", "Future"],
}


class DatasetLoader:
    """Charge et enrichit le dataset de référence."""

    def __init__(self, client: Optional[genai.Client] = None, model_name: str = "gemini-2.0-flash"):
        self.client = client
        self.model_name = model_name
        self._reference_startups: Optional[List[ReferenceStartup]] = None

    def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
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
                        wait = (attempt + 1) * 2
                        time.sleep(wait)
                        continue
                    if attempt == max_retries - 1:
                        continue
                    time.sleep(1)
        return ""

    def _parse_dataset_entries(self, max_entries: int = 200) -> List[Dict]:
        """Parse le dataset HuggingFace pour extraire les coordonnées GPS."""
        entries = []
        try:
            from datasets import load_dataset
            ds = load_dataset("hoangquang27/data_business", split="train")

            # Prendre un échantillon diversifié
            indices = list(range(len(ds)))
            random.seed(42)
            random.shuffle(indices)
            selected = indices[:max_entries]

            for idx in selected:
                row = ds[idx]
                response_text = row.get("response", "")

                # Parse: "X is located at ADDRESS, CITY city. postal code is XXXXX and latitude - longitude is LAT --LNG"
                lat_lng_match = re.search(
                    r'latitude\s*-\s*longitude\s+is\s+([\d\.\-]+)\s*-+([\d\.\-]+)',
                    response_text
                )
                name_match = re.search(r'^(.+?)\s+is\s+located\s+at', response_text)
                city_match = re.search(r',\s*(.+?)\s+city', response_text)

                if lat_lng_match and name_match:
                    entries.append({
                        "original_name": name_match.group(1).strip(),
                        "original_lat": float(lat_lng_match.group(1)),
                        "original_lng": float(lat_lng_match.group(2)),
                        "original_city": city_match.group(1).strip() if city_match else "Philadelphia",
                    })
        except Exception as e:
            print(f"[DatasetLoader] Erreur lors du chargement du dataset: {e}")
            # Fallback: generate entries from tech hubs directly
            for hub in US_TECH_HUBS:
                for i in range(10):
                    entries.append({
                        "original_name": f"Business_{hub['city']}_{i}",
                        "original_lat": hub["lat"] + random.uniform(-0.05, 0.05),
                        "original_lng": hub["lng"] + random.uniform(-0.05, 0.05),
                        "original_city": hub["city"],
                    })
        return entries

    def _generate_startup_name(self, sector: Sector) -> str:
        """Génère un nom de startup réaliste pour un secteur donné."""
        sector_words = SECTOR_NAMES.get(sector, SECTOR_NAMES[Sector.OTHER])
        prefix = random.choice(STARTUP_PREFIXES + sector_words)
        suffix = random.choice(STARTUP_SUFFIXES)
        return f"{prefix}{suffix}"

    def _enrich_entries_to_startups(self, entries: List[Dict]) -> List[ReferenceStartup]:
        """Transforme les entrées du dataset en startups de référence."""
        startups = []
        sectors = list(Sector)
        stages = list(GrowthStage)
        used_names = set()

        # Sector distribution weights (Silicon Valley = more fintech/saas)
        sector_weights = {
            Sector.FINTECH: 15, Sector.SAAS: 18, Sector.HEALTHTECH: 12,
            Sector.EDTECH: 8, Sector.ECOMMERCE: 10, Sector.AI_ML: 12,
            Sector.BIOTECH: 5, Sector.CYBERSECURITY: 6, Sector.CLEANTECH: 4,
            Sector.PROPTECH: 3, Sector.LOGISTICS: 3, Sector.FOODTECH: 4,
        }
        weighted_sectors = []
        for s, w in sector_weights.items():
            weighted_sectors.extend([s] * w)

        random.seed(42)

        for i, entry in enumerate(entries):
            # Assign to a US tech hub (redistribute from Philadelphia)
            hub = US_TECH_HUBS[i % len(US_TECH_HUBS)]
            lat = hub["lat"] + random.uniform(-0.08, 0.08)
            lng = hub["lng"] + random.uniform(-0.08, 0.08)

            sector = random.choice(weighted_sectors)

            # Generate unique name
            attempts = 0
            name = self._generate_startup_name(sector)
            while name in used_names and attempts < 20:
                name = self._generate_startup_name(sector)
                attempts += 1
            used_names.add(name)

            # Stage distribution (more seed/series_a)
            stage_weights = [0.1, 0.25, 0.25, 0.15, 0.05, 0.1, 0.1]
            stage = random.choices(stages, weights=stage_weights, k=1)[0]

            # Revenue based on stage
            revenue_ranges = {
                GrowthStage.PRE_SEED: (0, 50000),
                GrowthStage.SEED: (10000, 500000),
                GrowthStage.SERIES_A: (200000, 5000000),
                GrowthStage.SERIES_B: (2000000, 20000000),
                GrowthStage.SERIES_C_PLUS: (10000000, 100000000),
                GrowthStage.GROWTH: (5000000, 50000000),
                GrowthStage.MATURE: (20000000, 200000000),
            }
            rev_range = revenue_ranges.get(stage, (10000, 1000000))
            revenue = round(random.uniform(*rev_range), -2)

            # Employees based on stage
            emp_ranges = {
                GrowthStage.PRE_SEED: (1, 5),
                GrowthStage.SEED: (3, 20),
                GrowthStage.SERIES_A: (10, 80),
                GrowthStage.SERIES_B: (30, 250),
                GrowthStage.SERIES_C_PLUS: (100, 1000),
                GrowthStage.GROWTH: (50, 500),
                GrowthStage.MATURE: (200, 2000),
            }
            emp_range = emp_ranges.get(stage, (5, 50))
            employees = random.randint(*emp_range)

            # Funding based on stage
            funding_ranges = {
                GrowthStage.PRE_SEED: (0, 200000),
                GrowthStage.SEED: (100000, 2000000),
                GrowthStage.SERIES_A: (1000000, 15000000),
                GrowthStage.SERIES_B: (5000000, 50000000),
                GrowthStage.SERIES_C_PLUS: (20000000, 200000000),
                GrowthStage.GROWTH: (10000000, 100000000),
                GrowthStage.MATURE: (50000000, 500000000),
            }
            fund_range = funding_ranges.get(stage, (100000, 5000000))
            funding = round(random.uniform(*fund_range), -3)

            founded = random.randint(2010, 2024)

            startup = ReferenceStartup(
                name=name,
                sector=sector,
                location=hub["city"],
                state=hub["state"],
                latitude=round(lat, 6),
                longitude=round(lng, 6),
                employees=employees,
                revenue=revenue,
                growth_stage=stage,
                funding_total=funding,
                funding_rounds=[],
                description=f"{sector.value.replace('_', ' ').title()} startup based in {hub['city']}, {hub['state']}",
                founded_year=founded,
                key_metrics={},
            )
            startups.append(startup)

        return startups

    def _load_from_cache(self) -> Optional[List[ReferenceStartup]]:
        """Charge les startups depuis le cache local."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return [ReferenceStartup(**item) for item in data]
            except Exception as e:
                print(f"[DatasetLoader] Erreur lecture cache: {e}")
        return None

    def _save_to_cache(self, startups: List[ReferenceStartup]):
        """Sauvegarde les startups dans le cache local."""
        try:
            data = [s.model_dump() for s in startups]
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            print(f"[DatasetLoader] Cache sauvegardé: {len(startups)} startups")
        except Exception as e:
            print(f"[DatasetLoader] Erreur sauvegarde cache: {e}")

    def get_reference_startups(self, force_reload: bool = False) -> List[ReferenceStartup]:
        """
        Retourne la liste des startups de référence.
        Charge depuis le cache ou génère depuis le dataset.
        """
        if self._reference_startups and not force_reload:
            return self._reference_startups

        # Try cache first
        if not force_reload:
            cached = self._load_from_cache()
            if cached:
                self._reference_startups = cached
                print(f"[DatasetLoader] Chargé depuis cache: {len(cached)} startups")
                return cached

        # Parse dataset and enrich
        print("[DatasetLoader] Chargement et enrichissement du dataset...")
        entries = self._parse_dataset_entries(max_entries=200)
        startups = self._enrich_entries_to_startups(entries)

        # Cache the results
        self._save_to_cache(startups)
        self._reference_startups = startups
        print(f"[DatasetLoader] {len(startups)} startups de référence générées")
        return startups

    def get_startups_by_sector(self, sector: Sector) -> List[ReferenceStartup]:
        """Retourne les startups filtrées par secteur."""
        all_startups = self.get_reference_startups()
        return [s for s in all_startups if s.sector == sector]

    def get_stats(self) -> Dict:
        """Retourne des statistiques sur le dataset."""
        startups = self.get_reference_startups()
        from collections import Counter
        sectors = Counter(s.sector.value for s in startups)
        stages = Counter(s.growth_stage.value for s in startups)
        locations = Counter(s.location for s in startups)
        return {
            "total": len(startups),
            "by_sector": dict(sectors),
            "by_stage": dict(stages),
            "by_location": dict(locations.most_common(10)),
        }
