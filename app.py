import streamlit as st
import pandas as pd
from services.auth_service import AuthService
from models.user import UserRole
import os
import json

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
        role = st.selectbox("Rôle", ["entrepreneur", "etudiant"], key="reg_role")
        
        if st.button("S'inscrire"):
            if new_user and new_pwd:
                user = st.session_state.auth_service.register(new_user, new_pwd, role)
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
                mes_offres = content if isinstance(content, list) else [content]
        # Fallback pour données anciennes
        elif os.path.exists("extraction_results.json"):
            with open("extraction_results.json", "r", encoding="utf-8") as f:
                content = json.load(f)
                data = content if isinstance(content, list) else [content]
                mes_offres = [d for d in data if d.get("user_id") == st.session_state.user.id]
    except Exception as e:
        st.error(f"Erreur de lecture: {e}")

    # SECTION 1: TABLEAU
    st.subheader("📋 Mes Candidatures")
    if mes_offres:
        # Aplatir pour le tableau
        rows = []
        for offre in mes_offres:
            row = offre.get("data", {}).copy()
            row["Date"] = offre.get("date")
            row["ID"] = offre.get("id")
            rows.append(row)
        
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        
        # SECTION 2: DÉTAILS & APOSTS
        st.markdown("---")
        st.subheader("📢 Détails & Publications LinkedIn")
        
        # Sélecteur
        options = {f"#{d['id']} - {d['data'].get('job_title', 'Sans titre')} ({d['date']})": d for d in mes_offres}
        # Trier par ID décroissant (plus récent en haut)
        sorted_keys = sorted(options.keys(), key=lambda x: int(x.split('#')[1].split(' ')[0]), reverse=True)
        
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
                    st.success("Succès ! Allez voir le résultat dans le Tableau de Bord.")
                    st.balloons()
                except Exception as e:
                    status.update(label="❌ Erreur", state="error")
                    st.error(f"Une erreur est survenue : {e}")
        else:
            st.warning("Veuillez saisir une description.")

def dashboard_etudiant():
    st.title("🎓 Espace Étudiant")
    st.write(f"Bonjour **{st.session_state.user.username}**")
    st.info("Recherche de stages en cours de développement...")

def main():
    init_session()
    
    if not st.session_state.user:
        login_page()
    else:
        # Sidebar
        with st.sidebar:
            st.write(f"👤 **{st.session_state.user.username}**")
            st.caption(f"Rôle: {st.session_state.user.role}")
            if st.button("Déconnexion"):
                st.session_state.user = None
                st.rerun()
        
        # Router Dashboard
        if st.session_state.user.role == UserRole.ENTREPRENEUR.value:
            tab1, tab2 = st.tabs(["📊 Tableau de Bord", "➕ Nouvelle Recherche"])
            with tab1:
                dashboard_entrepreneur()
            with tab2:
                nouvelle_recherche_page()
        elif st.session_state.user.role == UserRole.ETUDIANT.value:
            dashboard_etudiant()
        else:
            st.error(f"Rôle inconnu: {st.session_state.user.role}")

if __name__ == "__main__":
    main()
