# -*- coding: utf-8 -*-
"""
StartupMatch AI — Interface Streamlit 7 étapes
Premium UI for Tunisian entrepreneurs
"""
import streamlit as st
import requests
import json
import time
from datetime import datetime

# ═══════════════════════════════════════════
# Page Configuration
# ═══════════════════════════════════════════

st.set_page_config(
    page_title="StartupMatch AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

API_URL = "http://localhost:8000"

# ═══════════════════════════════════════════
# Custom CSS — Premium Dark Theme
# ═══════════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global */
    .stApp {
        background: linear-gradient(135deg, #0f0a1e 0%, #1a1035 50%, #0d1b2a 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Hide default elements */
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding-top: 1rem; max-width: 1200px; }

    /* Hero Section */
    .hero-container {
        text-align: center; 
        padding: 2.5rem 1rem 1.5rem;
        animation: fadeIn 0.8s ease;
    }
    .hero-title {
        font-size: 2.8rem; font-weight: 800;
        background: linear-gradient(135deg, #818cf8, #c084fc, #f472b6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem; letter-spacing: -0.5px;
    }
    .hero-subtitle {
        color: #94a3b8; font-size: 1.05rem; font-weight: 300;
    }

    /* Step indicators */
    .steps-bar {
        display: flex; justify-content: center; gap: 8px;
        margin: 1.5rem 0; flex-wrap: wrap;
    }
    .step-pill {
        padding: 6px 16px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;
        transition: all 0.3s ease; cursor: default;
    }
    .step-pill.active {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white; box-shadow: 0 4px 15px rgba(99,102,241,0.4);
    }
    .step-pill.completed {
        background: rgba(34,197,94,0.2); color: #22c55e;
        border: 1px solid rgba(34,197,94,0.3);
    }
    .step-pill.pending {
        background: rgba(148,163,184,0.1); color: #64748b;
        border: 1px solid rgba(148,163,184,0.15);
    }

    /* Cards */
    .glass-card {
        background: rgba(30,27,75,0.6); border: 1px solid rgba(129,140,248,0.15);
        border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
        backdrop-filter: blur(12px); transition: all 0.3s ease;
    }
    .glass-card:hover { border-color: rgba(129,140,248,0.35); }
    .glass-card h3 {
        color: #e2e8f0; font-size: 1.15rem; margin-bottom: 0.8rem;
    }

    /* Metric cards */
    .metric-card {
        background: rgba(30,27,75,0.5); border: 1px solid rgba(129,140,248,0.1);
        border-radius: 12px; padding: 1.2rem; text-align: center;
    }
    .metric-value {
        font-size: 1.8rem; font-weight: 700; 
        background: linear-gradient(135deg, #818cf8, #c084fc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .metric-label { color: #94a3b8; font-size: 0.8rem; margin-top: 4px; }

    /* Match card (specific) */
    .match-card {
        background: rgba(30,27,75,0.5); border: 1px solid rgba(129,140,248,0.15);
        border-radius: 14px; padding: 1.2rem; margin-bottom: 0.8rem;
        transition: all 0.3s ease;
    }
    .match-card:hover { transform: translateY(-2px); border-color: rgba(129,140,248,0.4); }
    .match-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; }
    .match-name { color: #e2e8f0; font-size: 1rem; font-weight: 600; }

    /* Score badge */
    .score-badge {
        padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;
    }
    .score-high { background: rgba(34,197,94,0.2); color: #22c55e; }
    .score-med { background: rgba(234,179,8,0.2); color: #eab308; }
    .score-low { background: rgba(239,68,68,0.2); color: #ef4444; }

    /* Email card */
    .email-card {
        background: rgba(30,27,75,0.4); border: 1px solid rgba(129,140,248,0.12);
        border-radius: 12px; padding: 1.2rem; margin-bottom: 0.8rem;
    }
    .email-subject { color: #c084fc; font-weight: 600; font-size: 0.95rem; }
    .email-body {
        color: #cbd5e1; font-size: 0.85rem; line-height: 1.6;
        white-space: pre-wrap; margin-top: 0.6rem;
        background: rgba(15,10,30,0.4); padding: 1rem; border-radius: 8px;
    }

    /* Progress bar */
    .progress-container {
        background: rgba(30,27,75,0.4); border-radius: 20px; padding: 2px;
        margin: 0.3rem 0;
    }
    .progress-fill {
        height: 6px; border-radius: 20px;
        background: linear-gradient(90deg, #6366f1, #a78bfa);
        transition: width 0.5s ease;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important; border: none !important; border-radius: 12px !important;
        padding: 0.7rem 2rem !important; font-weight: 600 !important;
        font-size: 0.95rem !important; letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99,102,241,0.4) !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        background: rgba(30,27,75,0.6) !important; color: #e2e8f0 !important;
        border: 1px solid rgba(129,140,248,0.2) !important; border-radius: 10px !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #818cf8 !important;
        box-shadow: 0 0 0 2px rgba(129,140,248,0.2) !important;
    }

    /* Labels */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
        color: #c4b5fd !important; font-weight: 500 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px; background: rgba(30,27,75,0.3); border-radius: 12px; padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent; color: #94a3b8; border-radius: 8px;
        padding: 8px 16px; font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(30,27,75,0.4) !important; color: #c4b5fd !important;
        border-radius: 10px !important;
    }

    /* Misc text */
    .detail-label { color: #94a3b8; font-size: 0.8rem; }
    .detail-value { color: #e2e8f0; font-size: 0.9rem; font-weight: 500; }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; } }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
    .loading-pulse { animation: pulse 1.5s infinite; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════
# Session State
# ═══════════════════════════════════════════

def init_session_state():
    defaults = {
        "current_step": 0,
        "analysis_results": None,
        "is_analyzing": False,
        "user_input_data": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ═══════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════

STEPS = [
    ("👤", "Profil"),
    ("🔍", "Matching"),
    ("🗺️", "Carte"),
    ("📈", "Trajectoires"),
    ("💰", "Investisseurs"),
    ("✉️", "Emails"),
    ("📊", "Dashboard"),
]

def score_badge(score: float) -> str:
    if score >= 75:
        cls = "score-high"
    elif score >= 50:
        cls = "score-med"
    else:
        cls = "score-low"
    return f'<span class="score-badge {cls}">{score:.0f}%</span>'

def format_revenue(amount: float, currency: str = "€") -> str:
    if amount >= 1_000_000:
        return f"{currency}{amount/1_000_000:.1f}M"
    if amount >= 1_000:
        return f"{currency}{amount/1_000:.0f}K"
    return f"{currency}{amount:,.0f}"

def render_step_bar(active: int):
    pills = []
    for i, (icon, label) in enumerate(STEPS):
        if i < active:
            cls = "completed"
        elif i == active:
            cls = "active"
        else:
            cls = "pending"
        pills.append(f'<span class="step-pill {cls}">{icon} {label}</span>')
    st.markdown(f'<div class="steps-bar">{"".join(pills)}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════
# STEP 0: User Profiling Form
# ═══════════════════════════════════════════

def render_profiling_step():
    st.markdown("""
    <div class="glass-card">
        <h3>👤 Décrivez votre startup tunisienne</h3>
        <p style="color:#94a3b8; font-size:0.85rem;">
            Renseignez les informations de votre startup pour trouver des entreprises similaires aux USA.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("🏢 Nom de la startup", placeholder="Ex: TuniFin")
        sector = st.selectbox("🏭 Secteur", [
            "fintech", "healthtech", "edtech", "ecommerce", "saas",
            "biotech", "agritech", "cleantech", "proptech", "logistics",
            "foodtech", "insurtech", "mediatech", "cybersecurity", "ai_ml", "other"
        ], format_func=lambda x: x.replace("_", " ").title())
        location = st.text_input("📍 Ville", placeholder="Tunis, Paris, San Francisco", value="Tunis")
        employees = st.number_input("👥 Nombre d'employés", min_value=1, max_value=10000, value=5)

    with col2:
        stage = st.selectbox("📈 Stade de croissance", [
            "pre_seed", "seed", "series_a", "series_b",
            "series_c_plus", "growth", "mature"
        ], index=1, format_func=lambda x: x.replace("_", " ").title())
        revenue = st.number_input("💰 CA annuel (€)", min_value=0, max_value=100_000_000, value=0, step=10000)
        governorate = st.text_input("🗺️ Gouvernorat (optionnel)", placeholder="Tunis")

    description = st.text_area(
        "📝 Décrivez votre projet (min. 10 caractères)",
        placeholder="Nous développons une application mobile de paiement...",
        height=120
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Lancer l'analyse StartupMatch AI", use_container_width=True):
        if not description or len(description.strip()) < 10:
            st.error("⚠️ La description doit contenir au moins 10 caractères.")
            return

        st.session_state.is_analyzing = True
        st.session_state.user_input_data = {
            "sector": sector,
            "location": location,
            "latitude": 36.8065,
            "longitude": 10.1815,
            "employees": employees,
            "revenue": float(revenue),
            "description": description,
            "company_name": company_name or None,
            "stage": stage,
            "governorate": governorate or None,
        }

        with st.spinner(""):
            progress_placeholder = st.empty()
            status_placeholder = st.empty()

            steps_msgs = [
                "📋 Étape 1/7 — Initialisation du profil...",
                "🔍 Étape 2/7 — Recherche de startups US similaires...",
                "🗺️ Étape 3/7 — Préparation de la carte interactive...",
                "📈 Étape 4/7 — Analyse des trajectoires...",
                "💰 Étape 5/7 — Recherche d'investisseurs...",
                "✉️ Étape 6/7 — Génération des emails...",
                "📊 Étape 7/7 — Construction du tableau de bord...",
            ]

            # Show progress animation while API call runs
            progress_html = '<div class="progress-container"><div class="progress-fill" style="width: 0%"></div></div>'
            progress_placeholder.markdown(progress_html, unsafe_allow_html=True)
            status_placeholder.markdown(
                f'<p class="loading-pulse" style="color:#818cf8;text-align:center;font-size:0.9rem;">{steps_msgs[0]}</p>',
                unsafe_allow_html=True
            )

            try:
                response = requests.post(
                    f"{API_URL}/startupmatch",
                    json=st.session_state.user_input_data,
                    timeout=600
                )

                if response.status_code == 200:
                    st.session_state.analysis_results = response.json()
                    st.session_state.current_step = 1
                    st.session_state.is_analyzing = False
                    progress_placeholder.empty()
                    status_placeholder.empty()
                    st.rerun()
                elif response.status_code == 429:
                    st.error("⏳ Limite de quota Gemini atteinte. Réessayez dans quelques minutes.")
                else:
                    st.error(f"❌ Erreur serveur: {response.json().get('detail', 'Erreur inconnue')}")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Impossible de se connecter au serveur. Lancez `uvicorn main:app --port 8000`")
            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")

        st.session_state.is_analyzing = False

# ═══════════════════════════════════════════
# STEP 1: Matching Results
# ═══════════════════════════════════════════

def render_matching_step():
    data = st.session_state.analysis_results
    matches = data.get("matches", [])

    st.markdown("""
    <div class="glass-card">
        <h3>🔍 Startups US similaires trouvées</h3>
    </div>
    """, unsafe_allow_html=True)

    if not matches:
        st.warning("Aucun match trouvé. Essayez une autre description.")
        return

    # Summary metrics
    c1, c2, c3 = st.columns(3)
    avg_score = sum(m["similarity_score"] for m in matches) / len(matches)
    top_score = max(m["similarity_score"] for m in matches)
    c1.markdown(f'<div class="metric-card"><div class="metric-value">{len(matches)}</div><div class="metric-label">Matches trouvés</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-value">{avg_score:.0f}%</div><div class="metric-label">Score moyen</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-value">{top_score:.0f}%</div><div class="metric-label">Meilleur match</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    for match in matches:
        ref = match["reference_startup"]
        score = match["similarity_score"]
        badge = score_badge(score)
        reasons = match.get("match_reasons", [])

        funding_str = ""
        if ref.get("funding_total"):
            funding_str = f"<span class='detail-label'>🏦 Levée:</span> <span class='detail-value'>{format_revenue(ref['funding_total'])}</span>"

        reasons_html = " · ".join(f"✓ {r}" for r in reasons[:3]) if reasons else ""

        st.markdown(f"""
        <div class="match-card">
            <div class="match-header">
                <span class="match-name">🚀 {ref['name']}</span>
                {badge}
            </div>
            <div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin-bottom:0.5rem;">
                <span><span class="detail-label">📍</span> <span class="detail-value">{ref.get('location','')}, {ref.get('state','')}</span></span>
                <span><span class="detail-label">🏭</span> <span class="detail-value">{ref.get('sector','').replace('_',' ').title()}</span></span>
                <span><span class="detail-label">👥</span> <span class="detail-value">{ref.get('employees',0)}</span></span>
                <span><span class="detail-label">💰</span> <span class="detail-value">{format_revenue(ref.get('revenue',0))}</span></span>
                {funding_str}
            </div>
            <div style="color:#94a3b8; font-size:0.78rem;">{reasons_html}</div>
        </div>
        """, unsafe_allow_html=True)

        if match.get("match_explanation"):
            with st.expander(f"💡 Analyse Stratégique — {ref['name']}"):
                st.markdown(f"**Pourquoi ce modèle:** {match['match_explanation']}")
                
                if match.get("market_positioning"):
                     st.info(f"🎯 **Positionnement suggéré:** {match['market_positioning']}")

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("✅ **Points Forts (vs Marché):**")
                    for s in match.get("strengths", []):
                        st.markdown(f"- {s}")
                with c2:
                    st.markdown("⚠️ **Points Faibles / Risques:**")
                    for w in match.get("weaknesses", []):
                        st.markdown(f"- {w}")

                if match.get("innovative_ideas"):
                    st.markdown("---")
                    st.markdown("🚀 **Idées Innovantes pour gagner le marché:**")
                    for idea in match["innovative_ideas"]:
                         st.markdown(f"- {idea}")

# ═══════════════════════════════════════════
# STEP 2: Interactive Map
# ═══════════════════════════════════════════

def render_map_step():
    data = st.session_state.analysis_results

    st.markdown("""
    <div class="glass-card">
        <h3>🗺️ Carte interactive des startups similaires</h3>
    </div>
    """, unsafe_allow_html=True)

    try:
        from streamlit_folium import st_folium
        from map_generator import MapGenerator
        from models import MatchResult, UserStartupInput

        matches_data = data.get("matches", [])
        user_data = data.get("user_input", {})

        # Rebuild models for map
        matches_obj = []
        for md in matches_data:
            try:
                matches_obj.append(MatchResult(**md))
            except Exception:
                pass

        user_obj = None
        try:
            user_obj = UserStartupInput(**user_data)
        except Exception:
            pass

        if matches_obj:
            gen = MapGenerator()
            folium_map = gen.generate_competitor_map(matches_obj, user_obj)
            st_folium(folium_map, width=1100, height=550)
        else:
            st.info("Aucune donnée de carte disponible.")
    except ImportError:
        st.warning("📦 Installez `streamlit-folium` pour voir la carte: `pip install streamlit-folium`")
    except Exception as e:
        st.error(f"Erreur carte: {str(e)}")

# ═══════════════════════════════════════════
# STEP 3: Trajectory Analysis
# ═══════════════════════════════════════════

def render_trajectory_step():
    data = st.session_state.analysis_results
    trajectories = data.get("trajectories", [])

    st.markdown("""
    <div class="glass-card">
        <h3>📈 Analyse des trajectoires de croissance</h3>
    </div>
    """, unsafe_allow_html=True)

    if not trajectories:
        st.info("Aucune trajectoire disponible.")
        return

    for traj in trajectories:
        with st.expander(f"📈 {traj['startup_name']}", expanded=(trajectories.index(traj) == 0)):
            st.markdown(f"**Récit de croissance:**\n\n{traj['growth_narrative']}")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🔑 Facteurs clés de succès:**")
                for f in traj.get("key_success_factors", []):
                    st.markdown(f"- ✅ {f}")
            with c2:
                st.markdown("**⚠️ Risques identifiés:**")
                for r in traj.get("risk_warnings", []):
                    st.markdown(f"- ⚠️ {r}")

            if traj.get("funding_timeline"):
                st.markdown("**💰 Chronologie de financement:**")
                for ft in traj["funding_timeline"]:
                    st.markdown(f"- {ft.get('stage','')} — {ft.get('amount','')} ({ft.get('year','')})")

            st.markdown("---")
            st.markdown("**🇹🇳 Recommandations pour la Tunisie:**")
            for rec in traj.get("tunisian_recommendations", []):
                st.markdown(f"- 🎯 {rec}")

            if traj.get("adapted_strategy"):
                st.info(f"**Stratégie adaptée:** {traj['adapted_strategy']}")

# ═══════════════════════════════════════════
# STEP 4: Investors
# ═══════════════════════════════════════════

def render_investors_step():
    data = st.session_state.analysis_results
    investors = data.get("investors", [])

    st.markdown("""
    <div class="glass-card">
        <h3>💰 Investisseurs recommandés</h3>
    </div>
    """, unsafe_allow_html=True)

    if not investors:
        st.info("Aucun investisseur trouvé.")
        return

    for inv in investors[:10]:
        name = inv.get("name", "Investisseur")
        inv_type = inv.get("type", "").replace("_", " ").title()
        score = inv.get("match_score")
        score_html = score_badge(score) if score else ""

        st.markdown(f"""
        <div class="match-card">
            <div class="match-header">
                <span class="match-name">🏦 {name}</span>
                {score_html}
            </div>
            <div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin-bottom:0.4rem;">
                <span><span class="detail-label">Type:</span> <span class="detail-value">{inv_type}</span></span>
                <span><span class="detail-label">Ticket:</span> <span class="detail-value">{format_revenue(inv.get('investment_range_min',0))} - {format_revenue(inv.get('investment_range_max',0))}</span></span>
                <span><span class="detail-label">📍</span> <span class="detail-value">{inv.get('location','')}</span></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Détails — {name}"):
            st.write(inv.get("description", ""))
            cols = st.columns(2)
            with cols[0]:
                st.markdown("**Secteurs préférés:**")
                for ind in inv.get("preferred_industries", []):
                    st.markdown(f"- {ind}")
            with cols[1]:
                st.markdown("**Portfolio:**")
                for comp in inv.get("portfolio_companies", [])[:5]:
                    st.markdown(f"- {comp}")
            if inv.get("reasons_for_match"):
                st.markdown("**Pourquoi ce match:**")
                for r in inv["reasons_for_match"]:
                    st.markdown(f"- ✓ {r}")

# ═══════════════════════════════════════════
# STEP 5: Outreach Emails
# ═══════════════════════════════════════════

def render_emails_step():
    data = st.session_state.analysis_results
    emails = data.get("emails", [])

    st.markdown("""
    <div class="glass-card">
        <h3>✉️ Emails de prospection personnalisés</h3>
        <p style="color:#94a3b8;font-size:0.85rem;">
            Emails générés avec estimation de probabilité de réponse et timing optimal.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not emails:
        st.info("Aucun email généré.")
        return

    for email in emails:
        prob = email.get("response_probability", 0)
        priority = email.get("priority_level", "medium")
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")

        st.markdown(f"""
        <div class="email-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                <span style="color:#e2e8f0; font-weight:600;">
                    {priority_icon} {email.get('investor_name','')}
                </span>
                {score_badge(prob)}
            </div>
            <div class="email-subject">📧 {email.get('subject','')}</div>
            <div class="email-body">{email.get('body','')}</div>
            <div style="margin-top:0.8rem; display:flex; gap:1rem; font-size:0.78rem; color:#94a3b8;">
                <span>📅 Envoyer: {email.get('best_send_day','')} à {email.get('best_send_time','')}</span>
                <span>📊 Probabilité: {prob:.0f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if email.get("reasoning"):
            with st.expander(f"💡 Raisonnement — {email.get('investor_name','')}"):
                st.write(email["reasoning"])

# ═══════════════════════════════════════════
# STEP 6: Dashboard
# ═══════════════════════════════════════════

def render_dashboard_step():
    data = st.session_state.analysis_results
    dashboard = data.get("dashboard", {})
    user_metrics = dashboard.get("user_metrics", {})
    ref_metrics = dashboard.get("reference_metrics", {})
    comparison = dashboard.get("comparison_insights", [])

    st.markdown("""
    <div class="glass-card">
        <h3>📊 Tableau de bord comparatif</h3>
    </div>
    """, unsafe_allow_html=True)

    # Key metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'''<div class="metric-card">
        <div class="metric-value">{user_metrics.get("employees",0):.0f}</div>
        <div class="metric-label">Vos employés</div></div>''', unsafe_allow_html=True)
    c2.markdown(f'''<div class="metric-card">
        <div class="metric-value">{ref_metrics.get("avg_employees",0):.0f}</div>
        <div class="metric-label">Moy. référence</div></div>''', unsafe_allow_html=True)
    c3.markdown(f'''<div class="metric-card">
        <div class="metric-value">{format_revenue(user_metrics.get("revenue_tnd",0))}</div>
        <div class="metric-label">Votre CA</div></div>''', unsafe_allow_html=True)
    c4.markdown(f'''<div class="metric-card">
        <div class="metric-value">{format_revenue(ref_metrics.get("avg_revenue_usd",0))}</div>
        <div class="metric-label">CA moy. référence</div></div>''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Comparison insights
    st.markdown('<div class="glass-card"><h3>💡 Analyse comparative</h3>', unsafe_allow_html=True)
    for insight in comparison:
        st.markdown(f"- {insight}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Position summary
    if dashboard.get("position_summary"):
        st.info(f"📍 **Position:** {dashboard['position_summary']}")

    if dashboard.get("growth_gap_analysis"):
        st.warning(f"📈 **Écart de croissance:** {dashboard['growth_gap_analysis']}")

    # Recommended KPIs
    kpis = dashboard.get("recommended_kpis", [])
    if kpis:
        st.markdown("""
        <div class="glass-card">
            <h3>🎯 KPIs recommandés à suivre</h3>
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns(min(len(kpis), 5))
        for i, kpi in enumerate(kpis):
            cols[i % len(cols)].markdown(f"""
            <div class="metric-card" style="margin-bottom:0.5rem;">
                <div style="color:#c084fc;font-size:0.85rem;font-weight:600;">{kpi}</div>
            </div>
            """, unsafe_allow_html=True)

    # Execution time
    exec_time = data.get("execution_time", 0)
    if exec_time:
        st.caption(f"⏱️ Analyse complète en {exec_time}s")


# ═══════════════════════════════════════════
# Main Application
# ═══════════════════════════════════════════

def main():
    # Hero
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">🚀 StartupMatch AI</div>
        <div class="hero-subtitle">
            Intelligence artificielle pour les entrepreneurs tunisiens — 
            Trouvez vos modèles de référence et investisseurs aux USA (en €)
        </div>
    </div>
    """, unsafe_allow_html=True)

    # If we have results, show the step bar and tabs
    if st.session_state.analysis_results:
        data = st.session_state.analysis_results

        # Step bar
        render_step_bar(7)  # All complete

        # Navigation tabs
        tabs = st.tabs([
            f"{icon} {label}" for icon, label in STEPS[1:]  # Skip profile step
        ])

        with tabs[0]:
            render_matching_step()
        with tabs[1]:
            render_map_step()
        with tabs[2]:
            render_trajectory_step()
        with tabs[3]:
            render_investors_step()
        with tabs[4]:
            render_emails_step()
        with tabs[5]:
            render_dashboard_step()

        # Reset button
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Nouvelle analyse", use_container_width=True):
                st.session_state.analysis_results = None
                st.session_state.current_step = 0
                st.session_state.user_input_data = None
                st.rerun()
    else:
        # Show profile form
        render_step_bar(0)
        render_profiling_step()

if __name__ == "__main__":
    main()