import sys
sys.path.insert(0, '.')
import logging
logging.disable(logging.CRITICAL)

from agents.orchestrator import Orchestrator
import json
import os

# Nettoyer
if os.path.exists("extraction_results.json"):
    os.remove("extraction_results.json")

orchestrator = Orchestrator()

texte = "je suis un étudiant en troisieme année cycle ingénieur en technologies avancée , je suis à la recherche d'un stage pfe en intélligence artificielle"

print(f"Test avec: {texte}")
orchestrator.traiter_demande(texte)

if os.path.exists("extraction_results.json"):
    print("\n✅ Fichier extraction_results.json généré !")
    with open("extraction_results.json", "r", encoding="utf-8") as f:
        print(f.read())
else:
    print("\n❌ Fichier non généré.")
