import sys, json, re
sys.path.insert(0, '.')

# Supprimer les logs pour un output propre
import logging
logging.disable(logging.CRITICAL)

from agents.agent_comprehension import AgentComprehension

agent = AgentComprehension()

# Phrases de test
tests = [
    # Cas étudiant utilisateur
    "je suis un etudiant en deuxieme année cycle d'ingenieur en technologies avancée , je suis à la recherche d'un stage PFE",
    # Autre cas
    "étudiant en master 2 data science cherche stage de 6 mois à Paris"
]

print("=== DEBUT DES TESTS ETUDIANT ===\n")

for i, texte in enumerate(tests, 1):
    print(f"--- Test {i} ---")
    print(f"Entrée: {texte}")
    r = agent.process(texte)
    d = r.donnees_extraites
    
    # Affichage propre
    clean_dict = {k: v for k, v in d.items() if k != "additional_info"}
    print(json.dumps(clean_dict, indent=2, ensure_ascii=False))
    print("\n")

print("=== FIN DES TESTS ===")
