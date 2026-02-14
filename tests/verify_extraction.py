import sys, json, os

# Hack to disable logging if it uses standard logging
import logging
logging.disable(logging.CRITICAL)

try:
    # Adding parent dir to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.agent_comprehension import AgentComprehension

    agent = AgentComprehension()
    # Mocking the logger to be silent if it's not standard logging
    agent.logger.info = lambda *args: None
    agent.logger.success = lambda *args: None
    agent.logger.error = lambda *args: None
    agent.logger.data = lambda *args: None

    texte = "j'ai besoin de deux ingénieur informatique pour travailler dans l'entreprise QuantumForce cituée en tunis ,qui ont des compétence en IA et developpement web et qui metrisent SQL,react,nodejs,mongodb avec 3ans d'expérience, pour des contrat de type CDD d'une durée de 6 ans."

    r = agent.process(texte)
    d = r.donnees_extraites

    # Dump specifically the fields we care about
    with open('extraction_results.json', 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        
    print("Results written to extraction_results.json")

except Exception as e:
    with open('extraction_error.txt', 'w', encoding='utf-8') as f:
        f.write(str(e))
    print(f"Error: {e}")
