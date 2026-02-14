# AgenticHire 🤖

AgenticHire est une solution d'IA modulaire développée pour un hackathon. Elle automatise les processus de recrutement pour les entrepreneurs et la recherche de stage pour les étudiants.

## 🚀 Fonctionnalités

### Pour les Entrepreneurs 🏢
- **Publication automatique** : Postez des offres d'emploi sur LinkedIn.
- **Création de formulaires** : Génération automatique de Google Forms pour les candidats.
- **Scoring de candidats** : Analyse des CVs et matching avec les offres.
- **Communication automatisée** : Envoi d'emails de convocation ou de refus.

### Pour les Étudiants 🎓
- **Recherche intelligente** : Trouvez des offres de stage pertinentes via LinkedIn.
- **Analyse de CV** : Recevez des conseils pour optimiser votre candidature.

## 🛠 Architecture

Le projet est basé sur une architecture d'agents orchestrée par un **Orchestrator** central.

- **`main.py`** : Point d'entrée CLI (Texte ou Audio).
- **`agents/core/orchestrator.py`** : Cerveau du système.
- **`agents/core/comprehension`** : NLP pour comprendre l'intention.
- **`agents/core/audio`** : Transcription audio via Hugging Face.

## 📦 Installation

1.  **Cloner le dépôt**
    ```bash
    git clone https://github.com/votre-user/AgenticHire.git
    cd AgenticHire
    ```

2.  **Créer un environnement virtuel**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur Windows: venv\Scripts\activate
    ```

3.  **Installer les dépendances**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurer les variables d'environnement**
    Créez un fichier `.env` à la racine et ajoutez vos clés API :
    ```env
    HUGGINGFACE_API_KEY=votre_clé
    LINKEDIN_API_KEY=votre_clé
    # ... autres clés
    ```

## 🚀 Déploiement

Pour envoyer vos modifications sur GitHub, utilisez les scripts d'automatisation dans le dossier `scripts/` :

**Windows :**
```cmd
.\scripts\push_to_github.bat
```

**Linux / Mac / Git Bash :**
```bash
./scripts/push_to_github.sh
```

## ▶️ Utilisation

Lancez simplement le script principal :
```bash
python main.py
```
Suivez les instructions à l'écran pour interagir par texte ou audio.

## 📝 Auteurs
Projet réalisé par l'équipe **QuantumForce** pour le Hackathon.
