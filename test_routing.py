import sys
import os

# Ajout du dossier racine au path
sys.path.append(os.getcwd())

from agents.core.orchestrator import Orchestrator
from models.user import User

def test_router():
    print("--- Test Orchestrator Routing ---")
    
    orch = Orchestrator()
    user = User(id="test_user", username="Tester", password_hash="123", role="USER")
    orch.set_user(user)
    
    # Test 1: Student Intent
    print("\n1. Testing Student Intent...")
    resp_student = orch.handle_request("Je cherche un stage en Data Science", "test_user")
    print(f"Response: {resp_student}")
    if "candidat" in resp_student.lower():
        print("✅ SUCCESS: Detected Student")
    else:
        print("❌ FAILED: Did not detect Student")

    # Test 2: Entrepreneur Intent
    print("\n2. Testing Entrepreneur Intent...")
    resp_ent = orch.handle_request("Je veux recruter un développeur Python", "test_user")
    print(f"Response: {resp_ent}")
    if "recruteur" in resp_ent.lower():
        print("✅ SUCCESS: Detected Entrepreneur")
    else:
        print("❌ FAILED: Did not detect Entrepreneur")

    # Test 3: Ambiguous
    print("\n3. Testing Ambiguous Intent...")
    resp_amb = orch.handle_request("Bonjour", "test_user")
    print(f"Response: {resp_amb}")
    
if __name__ == "__main__":
    test_router()
