import sys, json, re
sys.path.insert(0, '.')

# Supprimer les logs pour un output propre
import logging
logging.disable(logging.CRITICAL)

from agents.agent_comprehension import AgentComprehension

agent = AgentComprehension()

# Phrases de test
tests = [
    # Cas utilisateur (avec fautes et structure complexe)
    "l'entrerpise QuantomForce cité à borj cedria ridah cherche 3 ingénieur en mecanique et electronique  ont des compétances en catia,proteus,rdm et electronique pour le développement d'un prototyoe d'une voiture electrique , la durée du projet est 2 ans en contrat CDD",
    # Autre cas complexe
    "Recrute 1 développeur embarqué maitrisant C++ et Linux pour une mission de 6 mois"
]

print("=== DEBUT DES TESTS ===\n")

for i, texte in enumerate(tests, 1):
    print(f"--- Test {i} ---")
    print(f"Entrée: {texte[:100]}...")
    r = agent.process(texte)
    d = r.donnees_extraites
    
    # Affichage propre
    clean_dict = {k: v for k, v in d.items() if k != "additional_info"}
    print(json.dumps(clean_dict, indent=2, ensure_ascii=False))
    print("\n")

print("=== FIN DES TESTS ===")
