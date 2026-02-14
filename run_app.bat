@echo off
echo ==================================================
echo 🚀 AgenticHire - Lancement de l'interface
echo ==================================================

echo.
echo 🔧 Vérification et installation des dépendances...
python -m pip install -r requirements.txt

echo.
echo ✅ Démarrage de l'application...
python -m streamlit run app.py

pause
