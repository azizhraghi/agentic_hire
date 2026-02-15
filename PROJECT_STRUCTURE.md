# AgenticHire - Structure du Projet

Ce document décrit la nouvelle architecture modulaire du projet.

## 📂 Dossiers Principaux (`agents/`)

### **`orchestrator.py`**
- **Rôle** : Le Chef d'Orchestre.
- **Fonction** : Reçoit la demande (texte), identifie le type d'utilisateur (Entrepreneur vs Étudiant) via `AgentComprehension`, et dirige vers le bon flux de travail.

### **`student/` (Nouveau Système Multi-Agents)**
- **`multi_agent_system.py`** : Système complet avec 7 agents spécialisés (Analyse CV, Scraping, Matching, etc.).
- **`interface.py`** : Interface Streamlit dédiée aux étudiants (Dashboard).
- **`tools/job_scraper.py`** : Scraper robuste (LinkedIn, RemoteOK, WeWorkRemotely, Adzuna).

### **`entrepreneur/`**
- **`agent_entrepreneur.py`** : Agent principal pour les recruteurs.
- **`agent_linkedin_post.py`** : Génération de posts LinkedIn.

### **`core/`**
- **`audio/`** : Transcription audio (Whisper/HuggingFace).
- **`comprehension/`** : Analyse d'intention.

## 📄 Fichiers Racine

- **`app.py`** : Point d'entrée principal (Interface Web Streamlit).
- **`cli_main.py`** : Ancienne interface en ligne de commande (Legacy).
- **`.env`** : Clés API.
- **`requirements.txt`** : Dépendances.

