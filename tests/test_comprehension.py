import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.agent_comprehension import AgentComprehension

def test_detection():
    """Test la détection du type d'utilisateur"""
    agent = AgentComprehension()
    
    tests = [
        ("Je cherche 3 développeurs Python", "ENTREPRENEUR"),
        ("Je voudrais un stage en marketing", "ETUDIANT"),
        ("J'ai besoin d'aide pour mes médicaments", "PERSONNE_AGEE"),
        ("Quel temps fait-il aujourd'hui?", "AUTRE")
    ]
    
    for texte, attendu in tests:
        result = agent.process(texte)
        print(f"✓ {texte[:30]:30} → {result.type_utilisateur.value} (attendu: {attendu})")
        assert result.type_utilisateur.value == attendu, f"Erreur: {texte}"

def test_extraction_recrutement():
    """Test l'extraction pour recrutement"""
    agent = AgentComprehension()
    
    texte = "Je cherche 2 ingénieurs data avec Python et SQL pour un CDI à Paris"
    result = agent.process(texte)
    
    print("\nExtraction recrutement:")
    print(f"Titre: {result.donnees_extraites['job_title']}")
    print(f"Nombre: {result.donnees_extraites['number_needed']}")
    print(f"Compétences: {result.donnees_extraites['skills_required']}")

if __name__ == "__main__":
    print("Tests de l'agent de compréhension")
    print("="*40)
    
    # test_detection()
    test_extraction_recrutement()
    
    print("\n✅ Tests terminés")