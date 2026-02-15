import requests
import json
import time

API_URL = "http://localhost:8001"

def test_startupmatch():
    print("Testing StartupMatch API...")
    
    payload = {
        "sector": "fintech",
        "location": "Tunis",
        "employees": 10,
        "revenue": 50000,
        "description": "Une plateforme de paiement mobile pour les non-bancarisés en Tunisie.",
        "stage": "seed",
        "governorate": "Tunis"
    }
    
    try:
        # We need to make sure the server is running. 
        # Since I cannot easily start the server and keep it running in background while running this script 
        # in the same turn without complex subprocess handling, 
        # I will assume the user or a separate process might run it, 
        # OR I can try to import the app and run it directly in this script.
        # Importing is safer for a quick check.
        
        from matching_engine import StartupMatcher
        from models import UserStartupInput, ReferenceStartup, Sector, GrowthStage
        from dataset_loader import DatasetLoader
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Skipping LLM test: GOOGLE_API_KEY not found.")
            return

        from google import genai
        client = genai.Client(api_key=api_key)
        
        matcher = StartupMatcher(client=client)
        loader = DatasetLoader(client=client)
        
        # Mock user input
        user_input = UserStartupInput(**payload)
        
        # Get some references (mock or load)
        # For speed, let's create a dummy reference
        ref = ReferenceStartup(
            name="Chime",
            sector=Sector.FINTECH,
            location="San Francisco",
            state="CA",
            latitude=37.77,
            longitude=-122.41,
            employees=100,
            revenue=50000000,
            growth_stage=GrowthStage.SERIES_C_PLUS,
            description="Neobank allowing no-fee banking."
        )
        
        print("Running find_similar_startups...")
        results = matcher.find_similar_startups(
            user_input=user_input, 
            reference_startups=[ref], 
            top_k=1, 
            generate_explanations=True
        )
        
        if not results:
            print("No results found.")
            return

        match = results[0]
        print(f"Match Score: {match.similarity_score}")
        print(f"Strengths: {match.strengths}")
        print(f"Weaknesses: {match.weaknesses}")
        print(f"Ideas: {match.innovative_ideas}")
        print(f"Positioning: {match.market_positioning}")
        
        if match.strengths and match.innovative_ideas:
            print("\nSUCCESS: New fields are populated!")
        else:
            print("\nFAILURE: New fields are empty.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_startupmatch()
