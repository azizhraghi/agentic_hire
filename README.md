# 🤖 AgenticHire

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![AI Agents](https://img.shields.io/badge/AI-Multi--Agent-orange)

**AgenticHire** est une plateforme de recrutement de nouvelle génération, propulsée par un écosystème **Multi-Agents**. 
Elle réunit **Recruteurs** et **Candidats** dans une interface conversationnelle unifiée, automatisant les tâches fastidieuses grâce à l'IA.

> 🚀 **Projet Hackathon** - Architecture Modulaire & Chat-First
## 👥 Équipe

- **KAROUI Mohamed Fares**
- **JOMNI May**
- **HRAGHI Mohamed Aziz**

---

## 💡 Le Problème
- **Recruteurs** : Perte de temps sur la rédaction d'offres, le tri des CVs et la gestion des emails.
- **Candidats** : Difficulté à trouver des offres pertinentes et à adapter leur CV à chaque poste.
- - **Entrepreneur** : cherche à faire une étude sur le marché et des investisseurs.

## ✨ La Solution AgenticHire

L'application détecte automatiquement votre rôle (via NLP) et active les agents appropriés.

### 👔 Espace Recruteur 
- **✍️ Génération de Contenu** : Création automatique de posts LinkedIn viraux optimisés pour l'engagement.
- **📊 Analyse de Candidatures** : Parsing de CVs, scoring de pertinence et tri automatique.
- **📅 Gestion Automatisée** : Envoi d'emails de convocation ou de refus personnalisés.
- **📝 Formulaires Intelligents** : Création de questionnaires de pré-qualification.

### 👔 Startup AI Agent
- **✍️ Project Overview** : Mission and target audience (entrepreneurs) Americain..
- **📊 Key Features** :  7-step AI pipeline (Profiling, Matching, Map, Trajectory, Investors, Emails, Dashboard).
- **📅 Gestion Automatisée** : Envoi d'emails de convocation ou de refus personnalisés.
- **📝 Formulaires Intelligents** : Création de questionnaires de pré-qualification.


### 🎓 Espace Candidat (Étudiant/Freelance)
*Propulsé par un système Multi-Agents (7 agents spécialisés)*
- **🧠 Analyse de Profil** : Extraction des compétences techniques et soft skills du CV.
- **🕵️ Recherche de Job IA** : Scraping temps réel sur 4 sources majeures :
  - **LinkedIn** (Offres publiques)
  - **RemoteOK** (API JSON)
  - **WeWorkRemotely** (Remote only)
  - **Adzuna** (Agrégateur)
- **🎯 Matching Intelligent** : Calcul de compatibilité (Score %) entre le CV et l'offre.
- **⚡ Optimisation** : Conseils pour améliorer le CV en fonction de l'offre visée.

---

## 🛠️ Stack Technique

- **Interface** : [Streamlit](https://streamlit.io/) (Python)
- **LLM & IA** : 
  - **DeepSeek V3** (Cerveau central)
  - **HuggingFace** (Modèles open-source pour tâches spécifiques)
  - **Mistral AI** (Support Multi-Agent)
- **Orchestration** : Architecture modulaire personnalisée
- **Scraping** : Beautiful Soup 4, Requests (avec rotation d'User-Agents)
- **Audio** : Whisper (via HuggingFace) pour la transcription vocale

---

## 🚀 Installation

### 1. Cloner le projet
```bash
git clone https://github.com/KAROUIFARES/AgenticHire.git
cd AgenticHire
```

### 2. Environnement Virtuel
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration
Créez un fichier `.env` à la racine :
```env
# Clés API requises
DEEPSEEK_API_KEY=votre_cle_deepseek
HUGGINGFACE_TOKEN=votre_token_hf
# Optionnel
MISTRAL_API_KEY=votre_cle_mistral
```

---

## ▶️ Utilisation

Lancez simplement l'application :
```bash
streamlit run app.py
```

1. **Authentification** : Créez un compte ou connectez-vous.
2. **Chat-First** : Parlez naturellement à l'IA.
   - *"Je cherche un développeur React senior"* 👉 Active l'Agent Recruteur
   - *"Trouve-moi un stage en IA à Paris"* 👉 Active l'Agent Candidat

---

## 🏗️ Architecture des Dossiers

```text
agents/
├── core/           # Orchestrateur, Compréhension, Audio
├── entrepreneur/   # Agents Recruteur (Post, Email, Scoring)
└── student/        # Système Multi-Agents Candidat (Scraper, Matcher)
    ├── tools/      # Scrapers (LinkedIn, WWR, RemoteOK)
    └── interface.py # Dashboard Étudiant
```

---

*Développé avec ❤️ pour le Hackathon*
