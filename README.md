# 🤖 AgenticHire

**AgenticHire** est une plateforme de recrutement intelligente propulsée par l'IA Multi-Agents.
Elle automatise le matching entre les **Recruteurs** (Entrepreneurs) et les **Candidats** (Étudiants/Freelances) via une interface unifiée.

> 🚀 **Projet Hackathon** - Architecture Modulaire & Interface Chat-First

---

## ✨ Fonctionnalités Clés

### 👔 Pour les Recruteurs
- **Génération de Post LinkedIn** : Création automatique de posts viraux pour vos offres.
- **Dispatching Intelligent** : Analyse, scoring et tri automatique des CVs reçus.
- **Invitations Automatiques** : Planification d'entretiens et envoi d'emails.

### 🎓 Pour les Candidats
- **Analyse de CV** : Extraction automatique des compétences et du profil.
- **Recherche de Job IA** : Scraping intelligent (RemoteOK, WeWorkRemotely) basé sur le profil.
- **Matching** : Calcul de score de pertinence pour chaque offre.

---

## 🛠️ Installation

1. **Cloner le projet**
   ```bash
   git clone https://github.com/votre-user/AgenticHire.git
   cd AgenticHire
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration (.env)**
   Créez un fichier `.env` à la racine :
   ```env
   DEEPSEEK_API_KEY=votre_cle
   HUGGINGFACE_TOKEN=votre_token
   # Optionnel (pour scraping LinkedIn avancé)
   LINKEDIN_USERNAME=...
   LINKEDIN_PASSWORD=...
   ```

---

## 🚀 Lancement

Lancez l'application Streamlit :
```bash
streamlit run app.py
```

L'interface s'ouvrira dans votre navigateur.
1. Créez un compte (identifiant/mot de passe).
2. Dites à l'IA ce que vous voulez faire :
   - *"Je cherche un développeur Python"* 👉 **Interface Recruteur**
   - *"Je cherche un stage en Data Science"* 👉 **Interface Candidat**

---

## 🏗️ Architecture Technique

Le projet repose sur une architecture **Multi-Agents** orchestrée :

- **Orchestrator** (`agents/core/`): Cerveau central qui comprend l'intention (NLP) et route vers le bon flux.
- **AgentEntrepreneur** (`agents/entrepreneur/`): Gère le cycle de vie recrutement (Création Offre -> Analyse -> Email).
- **AgentStudent** (`agents/student/`): Gère la recherche d'emploi (Analyse CV -> Scraping -> Matching).
- **Services** : Authentification (`auth_service`), Stockage (`JSON`), Logs (`AgenticLogger`).

---
*Fait avec ❤️ pour le Hackathon*
