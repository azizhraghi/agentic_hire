import sys, json
sys.path.insert(0, '.')

# Supprimer les logs pour un output propre
import logging
logging.disable(logging.CRITICAL)

from agents.agent_comprehension import AgentComprehension

agent = AgentComprehension()

texte = "j'ai besoin de deux ingénieur informatique pour travailler dans l'entreprise QuantumForce cituée en tunis ,qui ont des compétence en IA et developpement web et qui metrisent SQL,react,nodejs,mongodb avec 3ans d'expérience, pour des contrat de type CDD d'une durée de 6 ans."

r = agent.process(texte)
d = r.donnees_extraites

print("RESULTATS:")
for k, v in d.items():
    if k != "additional_info":
        print(f"  {k}: {v}")
