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
    st.title("🚀 Espace Recruteur")
    st.write(f"Bonjour **{st.session_state.user.username}**")
    
    # CHARGEMENT DES DONNÉES
    mes_offres = []
    try:
        user_file = f"data/{st.session_state.user.id}_data.json"
        if os.path.exists(user_file):
            with open(user_file, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, list):
                    # Aplatir si c'est une liste de listes (ex: [[{...}]])
                    flat_content = []
                    for item in content:
                        if isinstance(item, list):
                            flat_content.extend(item)
                        else:
                            flat_content.append(item)
                    mes_offres = flat_content
                else:
                    mes_offres = [content]
    except Exception as e:
        st.error(f"Erreur de lecture: {e}")

    # SECTION 1: TABLEAU
    st.subheader("📋 Mes Candidatures")
    
    # Préparer les options pour les listes déroulantes (utilisé dans plusieurs sections)
    options = {f"#{d['id']} - {d['data'].get('job_title', 'Sans titre')} ({d['date']})": d for d in mes_offres}
    sorted_keys = sorted(options.keys(), key=lambda x: int(x.split('#')[1].split(' ')[0]), reverse=True)

    if mes_offres:
        # Aplatir pour le tableau
        rows = []
        for offre in mes_offres:
            row = offre.get("data", {}).copy()
            row["Date"] = offre.get("date")
            row["ID"] = offre.get("id")
            rows.append(row)
        
        st.dataframe(pd.DataFrame(rows), width='stretch')
        
        # SECTION 2: DÉTAILS & APOSTS
        st.markdown("---")
        st.subheader("📢 Détails & Publications LinkedIn")
        
        choice = st.selectbox("🔍 Sélectionnez une offre pour voir le contenu généré :", sorted_keys)
        
        if choice:
            selected_offer = options[choice]
            artifacts = selected_offer.get("artifacts", {})
            data = selected_offer.get("data", {})
            
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.info("📝 **Post LinkedIn Généré**")
                post_content = artifacts.get("linkedin_post", "⚠️ Aucun contenu généré pour cette offre.")
                st.text_area("Contenu du post", post_content, height=400)
                
                url = artifacts.get("linkedin_url")
                if url:
                    st.success(f"✅ Publié sur LinkedIn : [Voir l'offre]({url})")
            
            with c2:
                st.warning("📋 **Formulaire Candidat**")
                form_link = artifacts.get("form_link")
                if form_link:
                     st.write(f"🔗 **Lien :** [{form_link}]({form_link})")
                     st.caption("Ce lien est inclus dans le post pour les candidats.")
                else:
                     st.error("Formulaire non généré.")
                
                st.markdown("### 🧩 Détails Extraits")
                st.json(data)

    else:
        st.info("Aucune offre trouvée. Créez votre première mission dans l'onglet 'Nouvelle Recherche' !")

    # SECTION 3: ACTIONS & DISPATCHING
    st.markdown("---")
    st.subheader("🤖 Dispatching & Recrutement")
    
    col_disp1, col_disp2 = st.columns([2, 1])
    
    with col_disp1:
        st.write("Lancez l'agent pour analyser les candidatures reçues et envoyer les convocations.")
        offer_to_dispatch = st.selectbox("Choisir une offre à traiter :", sorted_keys, key="dispatch_select")
        
        if st.button("👁️ Voir les candidats", type="secondary"):
            if offer_to_dispatch:
                selected_offer = options[offer_to_dispatch]
                offer_id = selected_offer.get("artifacts", {}).get("offer_id")
                
                if offer_id:
                   # Import dynamique
                    from agents.entrepreneur.agent_entrepreneur import AgentEntrepreneur
                    agent = AgentEntrepreneur()
                    candidats = agent.get_candidatures(offer_id)
                    
                    if candidats:
                        st.write(f"**{len(candidats)} Candidature(s) reçue(s) :**")
                        df_c = pd.DataFrame(candidats)
                        cols = ["date", "nom", "prenom", "email"]
                        if "date_rdv" in df_c.columns:
                            cols.append("date_rdv")
                        st.dataframe(df_c[cols], hide_index=True)
                    else:
                        st.warning("Aucune candidature pour le moment.")
                else:
                    st.warning("Offre sans ID compatible.")

        st.write("")
        if st.button("🚀 Lancer le Dispatching (Tri + Convocations)", type="primary"):
            if offer_to_dispatch:
                selected_offer = options[offer_to_dispatch]
                offer_id = selected_offer.get("artifacts", {}).get("offer_id") # On suppose que l'ID est dans artifacts
                
                # Si pas d'offer_id dans artifacts (anciennes données), on essaie de le déduire ou on avertit
                if not offer_id:
                     # Pour la compatibilité, on peut utiliser l'ID du timestamp si présent
                     st.warning("Cette offre est ancienne et n'a pas d'ID compatible pour le dispatching.")
                else:
                    with st.status("🧠 Agent Entrepreneur au travail...", expanded=True) as status:
                        st.write("📂 Lecture des candidatures...")
                        
                        # Import dynamique pour éviter cycles
                        from agents.entrepreneur.agent_entrepreneur import AgentEntrepreneur
                        agent = AgentEntrepreneur()
                        
                        resultats = agent.dispatcher_candidatures(offer_id)
                        
                        if resultats is None:
                            status.update(label="⚠️ Aucune candidature", state="error")
                            st.warning("Aucune candidature trouvée pour cette offre.")
                        else:
                            status.update(label="✅ Dispatching terminé !", state="complete")
                            st.success(f"Analyse terminée : {len(resultats)} candidats traités.")
                            
                            # Afficher les résultats
                            st.write("### 🏆 Classement IA & Planning")
                            df_results = pd.DataFrame(resultats)
                            if not df_results.empty:
                                cols_to_show = ["nom", "prenom", "email", "score"]
                                if "date_rdv" in df_results.columns:
                                    cols_to_show.append("date_rdv")
                                st.dataframe(df_results[cols_to_show], hide_index=True)
                            
                            st.caption("Les candidats avec un score > 75 ont reçu une convocation avec leur date d'entretien.")
                            
                            st.caption("Les candidats avec un score > 75 ont reçu une convocation par email.")

def nouvelle_recherche_page():
    st.header("🎯 Lancer une nouvelle mission")
    
    texte_demande = st.text_area("Décrivez votre besoin en recrutement...", 
                                 placeholder="Ex: Je cherche un Data Scientist Senior à Paris pour 6 mois...",
                                 height=150)
    
    if st.button("Lancer l'Agent IA 🤖", type="primary"):
        if texte_demande:
            with st.status("🚀 Traitement en cours...", expanded=True) as status:
                st.write("🧠 Analyse de la demande...")
                
                if "orchestrator" not in st.session_state:
                     from agents.core.orchestrator import Orchestrator
                     st.session_state.orchestrator = Orchestrator()
                
                st.session_state.orchestrator.set_user(st.session_state.user)
                
                try:
                    st.session_state.orchestrator.traiter_demande(texte_demande)
                    status.update(label="✅ Mission terminée !", state="complete", expanded=False)
                    st.success("✅ Succès ! Votre offre a été créée et le post LinkedIn généré.")
                    st.balloons()
                    
                    # Attendre un peu pour que l'utilisateur voie le message
                    import time
                    time.sleep(2)
                    
                    # Recharger automatiquement la page pour afficher les nouvelles données
                    st.rerun()
                    
                except Exception as e:
                    import traceback
                    status.update(label="❌ Erreur", state="error")
                    st.error(f"Une erreur est survenue : {e}")
                    with st.expander("🔍 Détails de l'erreur"):
                        st.code(traceback.format_exc())
        else:
            st.warning("Veuillez saisir une description.")

def dashboard_etudiant():
    st.title("🎓 Espace Étudiant")
    st.write(f"Bonjour **{st.session_state.user.username}**")
    st.info("Recherche de stages en cours de développement...")

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
            st.info("🔓 Espace Candidat Activé")
            with st.expander("🎓 ESPACE CANDIDAT", expanded=True):
                st.subheader("Mes Outils")
                uploaded_cv = st.file_uploader("1. Analysez votre CV (PDF)", type=["pdf"])
                if st.button("2. Lancer la recherche de stage"):
                    from agents.student.agent_student import AgentStudent
                    agent = AgentStudent()
                    # TODO: Connecter le vrai profil
                    jobs = agent.chercher_et_matcher({"primary_role": "Développeur Python", "technical_skills": ["Python", "Django"]})
                    st.write(f"🔎 {len(jobs)} offres trouvées !")
                    st.dataframe(jobs)

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
