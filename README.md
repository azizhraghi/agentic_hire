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
