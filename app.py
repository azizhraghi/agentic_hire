import streamlit as st
import pandas as pd
from services.auth_service import AuthService
from models.user import UserRole
import os
import json
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="AgenticHire",
    page_icon="🤖",
    layout="wide"
)

def init_session():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "auth_service" not in st.session_state:
        st.session_state.auth_service = AuthService()

def page_candidature():
    """Page publique pour les candidats"""
    st.title("📄 Postuler à une offre")
    
    # Récupérer l'ID de l'offre depuis l'URL
    query_params = st.query_params
    offer_id = query_params.get("offer_id", None)
    
    if not offer_id:
        st.warning("⚠️ Lien invalide. Aucun ID d'offre spécifié.")
        return

    st.info(f"Vous postulez pour l'offre : **{offer_id}**")
    
    with st.form("form_candidat"):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom")
            email = st.text_input("Email")
        with col2:
            prenom = st.text_input("Prénom")
            tel = st.text_input("Téléphone")
            
        cv_text = st.text_area("Copiez votre CV ou Lettre de Motivation ici", height=200)
        
        uploaded_file = st.file_uploader("Ou téléchargez votre CV (PDF)", type=["pdf"])
        
        submitted = st.form_submit_button("Envoyer ma candidature 🚀")
        
        if submitted:
            if not nom or not email or (not cv_text and not uploaded_file):
                st.error("Veuillez remplir les champs obligatoires (Nom, Email, CV).")
            else:
                # Sauvegarder la candidature
                candidature = {
                    "offer_id": offer_id,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "nom": nom,
                    "prenom": prenom,
                    "email": email,
                    "tel": tel,
                    "cv_text": cv_text,
                    "has_file": uploaded_file is not None
                }
                
                # Sauvegarde dans JSON central
                file_path = "data/candidatures.json"
                existing_apps = []
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing_apps = json.load(f)
                
                existing_apps.append(candidature)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(existing_apps, f, ensure_ascii=False, indent=2)
                    
                st.success("✅ Candidature envoyée avec succès ! Bonne chance 🍀")
                st.balloons()


def login_page():
    st.title("🔐 Connexion - AgenticHire")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Se connecter")
        username = st.text_input("Identifiant", key="login_user")
        password = st.text_input("Mot de passe", type="password", key="login_pwd")
        
        if st.button("Connexion"):
            user = st.session_state.auth_service.login(username, password)
            if user:
                st.session_state.user = user
                st.success(f"Bienvenue {user.username} ! Redirection...")
                st.rerun()
            else:
                st.error("Identifiants incorrects")

    with col2:
        st.subheader("Créer un compte")
        new_user = st.text_input("Nouvel identifiant", key="reg_user")
        new_pwd = st.text_input("Nouveau mot de passe", type="password", key="reg_pwd")
        # Role supprimé : Déterminé par l'usage
        
        if st.button("S'inscrire"):
            if new_user and new_pwd:
                user = st.session_state.auth_service.register(new_user, new_pwd)
                if user:
                    st.success("Compte créé ! Connectez-vous.")
                else:
                    st.error("Cet identifiant existe déjà.")
            else:
                st.warning("Remplissez tous les champs.")

def dashboard_entrepreneur():
    from agents.entrepreneur.recruiter_interface import render_recruiter_dashboard
    render_recruiter_dashboard()

def dashboard_etudiant():
    from agents.student.interface import render_student_dashboard
    render_student_dashboard()

def main():
    st.set_page_config(page_title="AgenticHire", page_icon="🤖", layout="wide")
    init_session()

    # --- PUBLIC ACCESS (CANDIDAT) ---
    # Récupérer les paramètres d'URL (Streamlit >= 1.30)
    query_params = st.query_params
    if query_params.get("page") == "candidat":
        page_candidature()
        return

    # --- PRIVATE ACCESS (LOGIN REQUIRED) ---
    if not st.session_state.user:
        login_page()
    else:
        # --- STATE MANAGEMENT ---
        if "workspace" not in st.session_state:
            st.session_state.workspace = None # 'entrepreneur', 'student', or None

        # --- SIDEBAR ---
        with st.sidebar:
            st.title("🤖 AgenticHire")
            st.write(f"👤 {st.session_state.user.username}")
            
            if st.button("🔄 Reset / Accueil"):
                st.session_state.workspace = None
                st.rerun()

            if st.button("Se déconnecter"):
                st.session_state.auth_service.logout()
                st.session_state.user = None
                st.session_state.workspace = None
                st.rerun()
            
            st.divider()
            st.caption("Mode Hackathon 🚀")

        # --- MAIN CONTENT ---
        st.title("💬 Assistant IA Recrutement")

        # 1. Historique du chat
        if "messages" not in st.session_state:
            st.session_state.messages = []
            st.session_state.messages.append({"role": "assistant", "content": "Bonjour ! Je suis votre agent IA. Dites-moi si vous cherchez un job ou si vous recrutez."})

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # 2. Espace de Travail (PERSISTANT)
        if st.session_state.workspace == 'entrepreneur':
            st.divider()
            st.info("🔓 Espace Recruteur Activé")
            with st.expander("🚀 TABLEAU DE BORD RECRUTEUR", expanded=True):
                dashboard_entrepreneur()
        
        elif st.session_state.workspace == 'student':
            st.divider()
            with st.expander("🎓 ESPACE CANDIDAT", expanded=True):
                dashboard_etudiant()

        # 3. Zone de saisie
        if user_input := st.chat_input("Votre demande..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            # Analyse
            from agents.core.orchestrator import Orchestrator
            orch = Orchestrator()
            orch.set_user(st.session_state.user) # Pass user context for correct data saving
            
            with st.spinner("🧠 Réflexion..."):
                response = orch.handle_request(user_input, st.session_state.user.id)
            
            # Mise à jour de la réponse et du state
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.write(response)

            # Détection de changement de contexte
            lower_resp = response.lower()
            if "recruteur" in lower_resp:
                st.session_state.workspace = 'entrepreneur'
                st.rerun()
            elif "candidat" in lower_resp:
                st.session_state.workspace = 'student'
                st.rerun()

if __name__ == "__main__":
    main()
