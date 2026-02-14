# AgenticHire - Structure du Projet

Ce document décrit la nouvelle architecture modulaire du projet.

## 📂 Dossiers Principaux (`agents/`)

### **`orchestrator.py`**
- **Rôle** : Le Chef d'Orchestre.
- **Fonction** : Reçoit la demande (texte), identifie le type d'utilisateur (Entrepreneur vs Étudiant) via `AgentComprehension`, et dirige vers le bon flux de travail.

### **`comprehension/`**
- **`agent_comprehension.py`** : Analyse le texte pour extraire les entités (compétences, dates, lieux, écoles).

### **`audio/`**
- **`agent_audio.py`** : Transcrit les fichiers audio en texte via Hugging Face.

### **`linkedin/`**
- **`agent_post.py`** : (Entrepreneur) Publie des offres d'emploi.
- **`agent_search.py`** : (Étudiant) Cherche des offres de stage.

### **`forms/`**
- **`agent_forms.py`** : (Entrepreneur) Crée des formulaires Google Forms pour les candidats et récupère les réponses.

### **`analysis/`**
- **`agent_scoring.py`** : (Entrepreneur) Analyse les candidatures, calcule un score de pertinence (matching CV vs Offre) et génère le fichier Excel/CSV des entretiens.

### **`communication/`**
- **`agent_email.py`** : (Entrepreneur) Envoie les convocations ou les refus par email.

## 📄 Fichiers Racine

- **`main.py`** : Point d'entrée. Initialise le pipeline, gère l'entrée (Micro/Clavier) et passe la main à l'Orchestrateur.
- **`.env`** : Clés API (Hugging Face, LinkedIn, Google, etc.).
- **`requirements.txt`** : Dépendances Python.
