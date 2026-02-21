"""
Recruiter Dashboard - Streamlit Interface
=================================================
AI-powered recruiter interface with provider selection.
Mirrors the student interface pattern.
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, timedelta


def render_recruiter_dashboard():
    """Main function to render the recruiter dashboard"""
    
    # ─── Session State Init ───
    if 'recruiter_job_data' not in st.session_state:
        st.session_state.recruiter_job_data = None
    if 'recruiter_linkedin_post' not in st.session_state:
        st.session_state.recruiter_linkedin_post = None
    if 'recruiter_scored_candidates' not in st.session_state:
        st.session_state.recruiter_scored_candidates = None
    if 'recruiter_use_mistral' not in st.session_state:
        st.session_state.recruiter_use_mistral = True
    if 'recruiter_use_huggingface' not in st.session_state:
        st.session_state.recruiter_use_huggingface = False
    if 'recruiter_api_key' not in st.session_state:
        st.session_state.recruiter_api_key = os.getenv('MISTRAL_API_KEY', '')
    if 'recruiter_hf_token' not in st.session_state:
        st.session_state.recruiter_hf_token = os.getenv('HUGGINGFACE_TOKEN', os.getenv('HF_TOKEN', ''))

    # ─── Header ───
    st.markdown("""
    <div style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 50%, #e67e22 100%); 
                padding: 2rem; border-radius: 16px; margin-bottom: 1.5rem; text-align: center;">
        <h1 style="color: white; margin:0;">🚀 Espace Recruteur & Entrepreneur</h1>
        <p style="color: rgba(255,255,255,0.9); margin-top: 0.5rem;">5 Agents IA Autonomes à votre service</p>
    </div>
    """, unsafe_allow_html=True)

    # ─── Sidebar: AI Provider ───
    with st.sidebar:
        st.markdown("#### ⚙️ Mode")
        
        providers = ["🤖 Mistral (Default)"]
        
        # Check for HuggingFace token
        if st.session_state.recruiter_hf_token:
            providers.append("🤗 HuggingFace (Free)")
        
        # Check for Gemini key
        if os.getenv('GOOGLE_API_KEY'):
            providers.append("🔮 Gemini")
        
        provider_choice = st.radio(
            "🔌 AI Provider",
            providers,
            key="recruiter_provider_radio"
        )
        
        # Update provider state
        if "Mistral" in provider_choice:
            st.session_state.recruiter_use_mistral = True
            st.session_state.recruiter_use_huggingface = False
        elif "HuggingFace" in provider_choice:
            st.session_state.recruiter_use_mistral = False
            st.session_state.recruiter_use_huggingface = True
        else:
            st.session_state.recruiter_use_mistral = False
            st.session_state.recruiter_use_huggingface = False

        # API Key input
        if st.session_state.recruiter_use_mistral:
            if not os.getenv('MISTRAL_API_KEY'):
                api_key = st.text_input("🔑 Mistral API Key", type="password", key="recruiter_mistral_key")
                if api_key:
                    st.session_state.recruiter_api_key = api_key
            else:
                st.success("✅ Mistral API Key loaded")
        elif st.session_state.recruiter_use_huggingface:
            if not st.session_state.recruiter_hf_token:
                hf_token = st.text_input("🔑 HuggingFace Token", type="password", key="recruiter_hf_key")
                if hf_token:
                    st.session_state.recruiter_hf_token = hf_token
            else:
                st.success("✅ HuggingFace Token loaded")
        else:
            if not os.getenv('GOOGLE_API_KEY'):
                api_key = st.text_input("🔑 Google API Key", type="password", key="recruiter_google_key")
                if api_key:
                    st.session_state.recruiter_api_key = api_key
            else:
                st.success("✅ Google API Key loaded")

    # ─── Main Tabs ───
    tab1, tab2, tab3 = st.tabs([
        "📝 Créer une Offre", 
        "👥 Analyser les Candidats", 
        "📋 Mes Offres"
    ])

    # ═══════════════════════════════════════════════════
    # TAB 1: CREATE JOB POSTING
    # ═══════════════════════════════════════════════════
    with tab1:
        st.subheader("🎯 Créer une Offre avec l'IA")
        
        st.info("💡 Décrivez votre besoin en langage naturel. L'IA génère automatiquement la fiche de poste et le post LinkedIn.")
        
        job_request = st.text_area(
            "Décrivez votre besoin en recrutement...",
            placeholder="Ex: Je recrute un AI Engineer senior pour ma startup AgenticHire à Tunis, salaire 10k/mois, il faut Python, ML, et NLP...",
            height=120,
            key="recruiter_job_input"
        )
        
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            generate_btn = st.button("🚀 Générer avec l'IA", type="primary", use_container_width=True)
        
        if generate_btn and job_request:
            # Get API key
            api_key = _get_api_key()
            
            if not api_key:
                st.error("⚠️ Veuillez configurer une clé API dans la barre latérale.")
            else:
                with st.status("🧠 Agents IA au travail...", expanded=True) as status:
                    from agents.entrepreneur.recruiter_agents import RecruiterCoordinator
                    
                    coordinator = RecruiterCoordinator(
                        api_key=api_key,
                        use_mistral=st.session_state.recruiter_use_mistral,
                        use_huggingface=st.session_state.recruiter_use_huggingface
                    )
                    
                    # Generate offer_id and form_url
                    offer_id = f"OFF-{int(datetime.now().timestamp())}"
                    base_url = "http://localhost:8501"
                    form_url = f"{base_url}/?page=candidat&offer_id={offer_id}"
                    
                    st.write("📝 Agent 1: Génération de la fiche de poste...")
                    st.write("📢 Agent 2: Création du post LinkedIn...")
                    
                    result = coordinator.create_job_posting(
                        raw_input=job_request,
                        form_url=form_url
                    )
                    
                    st.session_state.recruiter_job_data = result.get('job_data', {})
                    st.session_state.recruiter_linkedin_post = result.get('linkedin_post', '')
                    st.session_state.recruiter_offer_id = offer_id
                    st.session_state.recruiter_form_url = form_url
                    
                    status.update(label="✅ Offre générée avec succès !", state="complete")
        
        # Display results
        if st.session_state.recruiter_job_data:
            st.markdown("---")
            
            col_jd, col_li = st.columns(2)
            
            with col_jd:
                st.markdown("### 📄 Fiche de Poste Générée")
                jd = st.session_state.recruiter_job_data
                
                st.markdown(f"**Poste :** {jd.get('job_title', 'N/A')}")
                st.markdown(f"**Entreprise :** {jd.get('company_name', 'N/A')}")
                st.markdown(f"**Localisation :** {jd.get('location', 'N/A')}")
                st.markdown(f"**Contrat :** {jd.get('contract_type', 'N/A')}")
                st.markdown(f"**Expérience :** {jd.get('experience_level', 'N/A')}")
                st.markdown(f"**Salaire :** {jd.get('salary', 'N/A')}")
                
                if jd.get('skills_required'):
                    st.markdown("**Compétences :**")
                    for skill in jd['skills_required']:
                        st.markdown(f"  ✔️ {skill}")
                
                if jd.get('description'):
                    with st.expander("📋 Description complète"):
                        st.write(jd['description'])
                
                if jd.get('responsibilities'):
                    with st.expander("🎯 Responsabilités"):
                        for r in jd['responsibilities']:
                            st.write(f"• {r}")
                
                if jd.get('requirements'):
                    with st.expander("📌 Prérequis"):
                        for r in jd['requirements']:
                            st.write(f"• {r}")
            
            with col_li:
                st.markdown("### 📢 Post LinkedIn")
                post = st.session_state.recruiter_linkedin_post
                st.text_area("Contenu du post", post, height=400, key="linkedin_post_display")
                
                form_url = st.session_state.get('recruiter_form_url', '')
                if form_url:
                    st.success(f"🔗 **Lien candidature :** {form_url}")
                
                st.caption("📋 Copiez ce post et publiez-le sur LinkedIn !")
            
            # Save button
            if st.button("💾 Sauvegarder l'offre", type="primary"):
                _save_offer(st.session_state.user.id, st.session_state.recruiter_job_data, 
                           st.session_state.recruiter_linkedin_post,
                           st.session_state.get('recruiter_offer_id', ''),
                           st.session_state.get('recruiter_form_url', ''))
                st.success("✅ Offre sauvegardée !")
                st.balloons()

    # ═══════════════════════════════════════════════════
    # TAB 2: ANALYZE CANDIDATES
    # ═══════════════════════════════════════════════════
    with tab2:
        st.subheader("🧠 Analyse IA des Candidatures")
        
        # Load saved offers to select from
        offers = _load_user_offers(st.session_state.user.id)
        
        if not offers:
            st.info("📝 Aucune offre sauvegardée. Créez votre première offre dans l'onglet 'Créer une Offre'.")
        else:
            options = {
                f"#{o.get('id', '?')} - {o.get('data', {}).get('job_title', 'Sans titre')} ({o.get('date', 'N/A')})": o 
                for o in offers
            }
            
            selected_key = st.selectbox("🔍 Sélectionnez une offre :", list(options.keys()))
            selected_offer = options.get(selected_key, {})
            
            offer_id = selected_offer.get('artifacts', {}).get('offer_id', '')
            job_data = selected_offer.get('data', {})
            
            if not offer_id:
                st.warning("⚠️ Cette offre n'a pas d'ID compatible.")
            else:
                # Load candidates
                candidates = _load_candidates(offer_id)
                
                if not candidates:
                    st.info(f"📭 Aucune candidature reçue pour cette offre (ID: {offer_id}).")
                    st.markdown(f"🔗 Partagez ce lien : `http://localhost:8501/?page=candidat&offer_id={offer_id}`")
                else:
                    st.write(f"**{len(candidates)} candidature(s) reçue(s)**")
                    
                    # Quick overview table
                    df_preview = pd.DataFrame([{
                        "Nom": c.get('nom', ''),
                        "Prénom": c.get('prenom', ''),
                        "Email": c.get('email', ''),
                        "Date": c.get('date', ''),
                    } for c in candidates])
                    st.dataframe(df_preview, hide_index=True, use_container_width=True)
                    
                    # AI Scoring
                    if st.button("🧠 Lancer l'analyse IA des candidats", type="primary"):
                        api_key = _get_api_key()
                        
                        if not api_key:
                            st.error("⚠️ Veuillez configurer une clé API.")
                        else:
                            with st.status("🧠 Agents IA en action...", expanded=True) as status:
                                from agents.entrepreneur.recruiter_agents import RecruiterCoordinator
                                
                                coordinator = RecruiterCoordinator(
                                    api_key=api_key,
                                    use_mistral=st.session_state.recruiter_use_mistral,
                                    use_huggingface=st.session_state.recruiter_use_huggingface
                                )
                                
                                st.write(f"🧠 Agent 3: Analyse de {len(candidates)} candidat(s)...")
                                scored = coordinator.evaluate_candidates(candidates, job_data)
                                
                                st.write("📋 Agent 4: Planification des entretiens...")
                                scored = coordinator.plan_interviews(scored, job_data)
                                
                                st.session_state.recruiter_scored_candidates = scored
                                status.update(label="✅ Analyse terminée !", state="complete")
                    
                    # Display scored results
                    if st.session_state.recruiter_scored_candidates:
                        st.markdown("---")
                        st.markdown("### 🏆 Classement IA des Candidats")
                        
                        for i, cand in enumerate(st.session_state.recruiter_scored_candidates):
                            score = cand.get('score', 0)
                            
                            # Color code
                            if score >= 80:
                                color = "🟢"
                                badge = "Excellent"
                            elif score >= 60:
                                color = "🟡"
                                badge = "Bon"
                            else:
                                color = "🔴"
                                badge = "Faible"
                            
                            with st.expander(
                                f"{color} #{i+1} — {cand.get('nom', 'N/A')} {cand.get('prenom', '')} — "
                                f"Score: **{score}/100** ({badge})",
                                expanded=(i == 0)
                            ):
                                col_s1, col_s2 = st.columns(2)
                                
                                with col_s1:
                                    st.metric("Score IA", f"{score}/100")
                                    st.write(f"**Recommandation :** {cand.get('recommendation', 'N/A')}")
                                    st.write(f"**Priorité entretien :** {cand.get('interview_priority', 'N/A')}")
                                    st.write(f"**Raisonnement :** {cand.get('reasoning', 'N/A')}")
                                    
                                    if cand.get('strengths'):
                                        st.write("**Points forts :**")
                                        for s in cand['strengths']:
                                            st.write(f"  ✅ {s}")
                                    
                                    if cand.get('gaps'):
                                        st.write("**Points à vérifier :**")
                                        for g in cand['gaps']:
                                            st.write(f"  ⚠️ {g}")
                                
                                with col_s2:
                                    plan = cand.get('interview_plan', {})
                                    if plan:
                                        st.write("**📋 Questions d'entretien suggérées :**")
                                        
                                        if plan.get('technical_questions'):
                                            st.write("*Questions techniques :*")
                                            for q in plan['technical_questions']:
                                                st.write(f"  🔧 {q}")
                                        
                                        if plan.get('behavioral_questions'):
                                            st.write("*Questions comportementales :*")
                                            for q in plan['behavioral_questions']:
                                                st.write(f"  🤝 {q}")
                                        
                                        if plan.get('areas_to_probe'):
                                            st.write("*Zones à approfondir :*")
                                            for a in plan['areas_to_probe']:
                                                st.write(f"  🔍 {a}")
                                        
                                        st.write(f"⏱️ **Durée recommandée :** {plan.get('recommended_duration', 'N/A')}")

    # ═══════════════════════════════════════════════════
    # TAB 3: MY OFFERS
    # ═══════════════════════════════════════════════════
    with tab3:
        st.subheader("📋 Mes Offres Publiées")
        
        offers = _load_user_offers(st.session_state.user.id)
        
        if not offers:
            st.info("Aucune offre trouvée. Créez votre première offre dans l'onglet 'Créer une Offre' !")
        else:
            # Summary table
            rows = []
            for o in offers:
                data = o.get('data', {})
                rows.append({
                    "ID": o.get('id', ''),
                    "Date": o.get('date', ''),
                    "Poste": data.get('job_title', 'N/A'),
                    "Entreprise": data.get('company_name', 'N/A'),
                    "Lieu": data.get('location', 'N/A'),
                    "Contrat": data.get('contract_type', 'N/A'),
                })
            
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            
            # Detail view
            options = {
                f"#{o.get('id', '?')} - {o.get('data', {}).get('job_title', 'Sans titre')}": o 
                for o in offers
            }
            
            choice = st.selectbox("🔍 Détails de l'offre :", list(options.keys()), key="offer_detail_select")
            
            if choice:
                sel = options[choice]
                artifacts = sel.get('artifacts', {})
                
                col_d1, col_d2 = st.columns(2)
                
                with col_d1:
                    st.info("📋 **Données de l'offre**")
                    st.json(sel.get('data', {}))
                
                with col_d2:
                    st.info("📢 **Post LinkedIn**")
                    post = artifacts.get('linkedin_post', 'Aucun post généré.')
                    st.text_area("Post", post, height=300, key=f"post_{sel.get('id')}")
                    
                    form = artifacts.get('form_link', '')
                    if form:
                        st.success(f"🔗 [Lien candidature]({form})")


# ═══════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════

def _get_api_key() -> str:
    """Get the current API key based on selected provider"""
    if st.session_state.recruiter_use_huggingface:
        return st.session_state.recruiter_hf_token
    return st.session_state.recruiter_api_key or os.getenv('MISTRAL_API_KEY') or os.getenv('GOOGLE_API_KEY', '')


def _save_offer(user_id: str, job_data: dict, linkedin_post: str, offer_id: str, form_url: str):
    """Save offer to user's data file"""
    if not os.path.exists("data"):
        os.makedirs("data")
    
    fichier = f"data/{user_id}_data.json"
    
    enregistrement = {
        "id": None,
        "user_id": user_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type_flux": "entrepreneur",
        "data": job_data,
        "artifacts": {
            "offer_id": offer_id,
            "form_link": form_url,
            "linkedin_post": linkedin_post,
            "linkedin_url": f"https://www.linkedin.com/jobs/view/{abs(hash(offer_id)) % 100000}"
        }
    }
    
    try:
        historique = []
        if os.path.exists(fichier):
            with open(fichier, "r", encoding="utf-8") as f:
                contenu = json.load(f)
                historique = contenu if isinstance(contenu, list) else [contenu]
        
        enregistrement["id"] = len(historique) + 1
        historique.append(enregistrement)
        
        with open(fichier, "w", encoding="utf-8") as f:
            json.dump(historique, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Erreur sauvegarde: {e}")


def _load_user_offers(user_id: str) -> list:
    """Load all offers for a user"""
    fichier = f"data/{user_id}_data.json"
    
    if not os.path.exists(fichier):
        return []
    
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            content = json.load(f)
            if isinstance(content, list):
                # Flatten nested lists
                flat = []
                for item in content:
                    if isinstance(item, list):
                        flat.extend(item)
                    else:
                        flat.append(item)
                return flat
            return [content]
    except Exception:
        return []


def _load_candidates(offer_id: str) -> list:
    """Load candidates for a specific offer"""
    file_path = "data/candidatures.json"
    
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)
            all_apps = content if isinstance(content, list) else []
            return [app for app in all_apps if app.get("offer_id") == offer_id]
    except Exception:
        return []
