"""Test for Agent Comprehension using the new Mistral API key"""
import os, logging
logging.disable(logging.CRITICAL)

from agents.core.comprehension.agent_comprehension import AgentComprehension

agent = AgentComprehension()
print(f"Provider detected: {agent.provider}")
print(f"Mistral Key present: {'YES' if os.getenv('MISTRAL_API_KEY') else 'NO'}")

test_cases = [
    "looking for an internship",
    "I want to hire 3 developers",
]

for text in test_cases:
    print(f"\nINPUT: {text}")
    result = agent.process(text)
    print(f"  RESULT: {result.type_utilisateur.value} (conf={result.confiance:.2f})")
