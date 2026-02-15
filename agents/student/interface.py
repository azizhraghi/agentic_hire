"""
AI Job Scout Dashboard - Student Interface
=================================================
Refactored for AgenticHire
"""

import streamlit as st
import pandas as pd
import os
import plotly.express as px
from pypdf import PdfReader
from agents.student.multi_agent_system import CVAnalyzerAgent, CoordinatorAgent
from agents.student.matcher_fix import patch_matcher_agent, patch_job_analyzer

# Helper functions
def extract_cv_text(pdf_file):
    """Extract text from PDF"""
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def deduplicate_jobs(jobs):
    """Remove duplicate jobs by (title, company), keeping the higher match score"""
    seen = {}
    for job in jobs:
        key = (job.get('title', '').lower().strip(), job.get('company', '').lower().strip())
        if key not in seen or job.get('ai_match_score', 0) > seen[key].get('ai_match_score', 0):
            seen[key] = job
    return list(seen.values())

# Source badge helper
SOURCE_BADGE_MAP = {
    'LinkedIn': ('🟦', 'source-linkedin'),
    'Indeed': ('🟪', 'source-indeed'),
    'RemoteOK': ('🟩', 'source-remoteok'),
    'Adzuna': ('🟧', 'source-adzuna'),
    'Google Jobs': ('🟥', 'source-google'),
    'Google Search': ('🟥', 'source-google'),
    'Demo': ('🎬', 'source-demo'),
}

def get_source_badge(source: str) -> str:
    """Get HTML badge for a job source"""
    emoji, css_class = SOURCE_BADGE_MAP.get(source, ('📌', 'source-default'))
    return f" <span class='source-badge {css_class}'>{emoji} {source}</span>"

def show_job_card(job, index):
    """Display job card"""
    match_result = job.get('ai_analysis', {}).get('match_result', {})
    # Use ai_match_score (always set) as primary, fallback to nested path
    score = job.get('ai_match_score', match_result.get('overall_match_score', 0))
    
    if score >= 80:
        card_class = "match-high"
        emoji = "🎯"
    elif score >= 60:
        card_class = "match-medium"
        emoji = "👍"
    else:
        card_class = "match-low"
        emoji = "👎"
    
    st.markdown(f"<div class='{card_class}'>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        source_badge = get_source_badge(job.get('source', 'Unknown'))
        st.markdown(f"### {emoji} {job.get('title', 'N/A')}{source_badge}", unsafe_allow_html=True)
        st.markdown(f"**🏢 {job.get('company', 'N/A')}** | 📍 {job.get('location', 'N/A')}")
    
    with col2:
        st.markdown("**Match Score**")
        st.markdown(f"# {score}%")
    
    with col3:
        st.markdown("**Priority**")
        priority = job.get('ai_priority', match_result.get('priority', 'Consider'))
        st.markdown(f"# {priority}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.expander("🔍 Full Details"):
        tab1, tab2, tab3 = st.tabs(["Match Analysis", "Skills", "Actions"])
        
        with tab1:
            st.markdown(f"**Recommendation:** {match_result.get('recommendation', 'N/A')}")
            if match_result.get('application_tips'):
                st.markdown("**💡 Tips:**")
                for tip in match_result['application_tips']:
                    st.markdown(f"- {tip}")
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Matching:**")
                for skill in match_result.get('matching_skills', [])[:8]:
                    st.markdown(f"✓ {skill}")
            with col2:
                st.markdown("**❌ Missing:**")
                for skill in match_result.get('missing_skills', [])[:8]:
                    st.markdown(f"✗ {skill}")
        
        with tab3:
            if st.button(f"✍️ Generate Application", key=f"gen_{index}"):
                st.session_state.selected_job = job
                st.session_state.page = 'generate'
                st.rerun()
            if job.get('url') and job.get('url') != '#':
                st.markdown(f"[🔗 View Job Posting]({job['url']})")

def render_student_dashboard():
    """Main function to render student dashboard"""
    
    # Enhanced CSS
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .source-badge {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            display: inline-block;
            margin-left: 8px;
            color: white;
        }
        .source-linkedin { background: #0077B5; }
        .source-indeed { background: #6C3BAA; }
        .source-remoteok { background: #28a745; }
        .source-adzuna { background: #E67E22; }
        .source-google { background: #DB4437; }
        .source-demo { background: #ff6b6b; }
        .source-default { background: #6c757d; }
        .match-high {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-left: 5px solid #28a745;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .match-medium {
            background-color: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .match-low {
            background-color: #f8d7da;
            border-left: 5px solid #dc3545;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    # Session state initialization
    if 'api_key' not in st.session_state:
        st.session_state.api_key = os.getenv('GOOGLE_API_KEY', '')
    if 'cv_text' not in st.session_state:
        st.session_state.cv_text = None
    if 'cv_analysis' not in st.session_state:
        st.session_state.cv_analysis = None
    if 'jobs' not in st.session_state:
        st.session_state.jobs = None
    if 'selected_job' not in st.session_state:
        st.session_state.selected_job = None
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'demo_mode' not in st.session_state:
        st.session_state.demo_mode = False 
    if 'use_huggingface' not in st.session_state:
        st.session_state.use_huggingface = False
    if 'hf_model' not in st.session_state:
        st.session_state.hf_model = "mistralai/Mistral-7B-Instruct-v0.2"
    if 'hf_token' not in st.session_state:
        st.session_state.hf_token = os.getenv('HUGGINGFACE_TOKEN', os.getenv('HF_TOKEN', ''))
    if 'use_mistral' not in st.session_state:
        st.session_state.use_mistral = True
    if 'mistral_model' not in st.session_state:
        st.session_state.mistral_model = "mistral-small-latest"
    if 'mistral_key' not in st.session_state:
        st.session_state.mistral_key = os.getenv('MISTRAL_API_KEY', '')

    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Mode")
        demo_mode = st.toggle(
            "🎬 Demo Mode",
            value=st.session_state.demo_mode,
            help="Use high-quality demo jobs for reliable presentations"
        )
        if demo_mode != st.session_state.demo_mode:
            st.session_state.demo_mode = demo_mode
            st.rerun()
        
        if demo_mode:
            st.info("🎬 Demo Mode: Using pre-loaded jobs")
        else:
            st.success("🌐 Live Mode: Real web scraping")
        
        st.markdown("---")
        
        # AI PROVIDER SELECTION
        st.markdown("### 🧠 AI Provider")
        
        providers = ["💎 Gemini (20/day)"]
        providers.append("🤗 HuggingFace (1000/day, FAST!)")
        providers.append("🔷 Mistral AI (Recommended)")
        
        if st.session_state.use_mistral:
            current_index = providers.index("🔷 Mistral AI (Recommended)") if "🔷 Mistral AI (Recommended)" in providers else 0
        elif st.session_state.use_huggingface:
            current_index = providers.index("🤗 HuggingFace (1000/day, FAST!)")
        else:
            current_index = 0
        
        provider_choice = st.radio(
            "Select Provider:",
            providers,
            index=current_index,
            help="Mistral AI recommended for best quality"
        )
        
        new_use_hf = "HuggingFace" in provider_choice
        new_use_mistral = "Mistral" in provider_choice
        new_use_gemini = "Gemini" in provider_choice
        
        if (new_use_hf != st.session_state.use_huggingface or 
            new_use_mistral != st.session_state.use_mistral):
            st.session_state.use_huggingface = new_use_hf
            st.session_state.use_mistral = new_use_mistral if new_use_mistral else (not new_use_hf and not new_use_gemini)
            st.rerun()
        
        # Provider specific settings
        if st.session_state.use_mistral:
            st.success("🔷 Using Mistral AI")
            if not st.session_state.mistral_key:
                st.warning("⚠️ Mistral API Key Required")
                mistral_key = st.text_input("Mistral API Key", type="password")
                if mistral_key:
                    st.session_state.mistral_key = mistral_key
                    st.rerun()
            
        elif st.session_state.use_huggingface:
            st.success("✅ FAST & FREE! (~1000/day)")
            if not st.session_state.hf_token:
                st.info("Optional: Add HF token for higher limits")
                hf_token = st.text_input("HuggingFace Token", type="password")
                if hf_token:
                    st.session_state.hf_token = hf_token
                    st.rerun()
        
        else:
            st.info("💎 Using Gemini (20/day limit)")
        
        st.markdown("---")
        
        # Navigation
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
        
        if st.button("📄 Upload CV", use_container_width=True):
            st.session_state.page = 'upload'
            st.rerun()
        
        if st.button("🚀 Find Jobs", use_container_width=True):
            st.session_state.page = 'search'
            st.rerun()

    # Main Content Area
    if st.session_state.page == 'home':
        st.markdown("""
        <div class='main-header'>
            <h1>🎓 Espace Étudiant & Candidat</h1>
            <p>7 Agents IA Autonomes à votre service</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📤 Upload CV", use_container_width=True, type="primary"):
                st.session_state.page = 'upload'
                st.rerun()
        with col2:
            if st.button("🔍 Find Jobs", use_container_width=True, type="primary"):
                st.session_state.page = 'search'
                st.rerun()
        with col3:
            mode_label = "🎬 Demo Mode ON" if st.session_state.demo_mode else "🌐 Live Mode"
            st.info(mode_label)
        
        st.markdown("---")
        
        if st.session_state.jobs:
            st.markdown("## 🎯 Vos Offres Matchées")
            
            jobs = st.session_state.jobs
            col1, col2, col3 = st.columns(3)
            
            total = len(jobs)
            high = len([j for j in jobs if j.get('ai_match_score', 0) >= 80])
            avg = sum(j.get('ai_match_score', 0) for j in jobs) / total if total > 0 else 0
            
            col1.metric("Total Jobs", total)
            col2.metric("🎯 High Match", high)
            col3.metric("📈 Avg Score", f"{avg:.0f}%")
            
            st.markdown("---")
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                min_score = st.slider("Min Match Score", 0, 100, 0)
            with col2:
                available_sources = sorted(set(j.get('source', 'Unknown') for j in jobs))
                source_filter = st.multiselect(
                    "Source Filter",
                    available_sources,
                    default=available_sources
                )
            
            # Filter and display
            filtered = [j for j in jobs 
                        if j.get('ai_match_score', 0) >= min_score 
                        and j.get('source', 'Unknown') in source_filter]
            filtered.sort(key=lambda x: x.get('ai_match_score', 0), reverse=True)
            
            # CSV Export button
            export_data = [{
                'Title': j.get('title', ''),
                'Company': j.get('company', ''),
                'Location': j.get('location', ''),
                'Source': j.get('source', ''),
                'Match Score': j.get('ai_match_score', 0),
                'Priority': j.get('ai_priority', 'Unknown'),
                'URL': j.get('url', '')
            } for j in filtered]
            
            csv_data = pd.DataFrame(export_data).to_csv(index=False)
            st.download_button("📥 Export CSV", csv_data, "matched_jobs.csv", "text/csv", use_container_width=True)
            
            for idx, job in enumerate(filtered[:20]):
                show_job_card(job, idx)
            
            # Analytics
            st.markdown("---")
            st.markdown("## 📊 Analytics")
            
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                scores = [j.get('ai_match_score', 0) for j in jobs]
                fig_hist = px.histogram(
                    x=scores, nbins=10,
                    labels={'x': 'Match Score (%)', 'y': 'Number of Jobs'},
                    title='📈 Score Distribution',
                    color_discrete_sequence=['#667eea']
                )
                fig_hist.update_layout(bargap=0.1, showlegend=False, height=300)
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with chart_col2:
                # Skill gap analysis
                all_missing = []
                for j in jobs:
                    mr = j.get('ai_analysis', {}).get('match_result', {})
                    all_missing.extend(mr.get('missing_skills', []))
                
                if all_missing:
                    from collections import Counter
                    top_miss = Counter(all_missing).most_common(8)
                    fig_miss = px.bar(
                        x=[c for _, c in top_miss], y=[s for s, _ in top_miss],
                        orientation='h', title='❌ Top Missing Skills (Gaps)',
                        labels={'x': 'Frequency', 'y': ''},
                        color_discrete_sequence=['#dc3545']
                    )
                    fig_miss.update_layout(height=300, yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_miss, use_container_width=True)
        
        else:
            st.markdown("## 👋 Commencez ici")
            st.info("📤 Uploadez votre CV pour démarrer la recherche autonome !")

    elif st.session_state.page == 'upload':
        st.markdown("# 📄 Upload Your CV")
        st.markdown("---")
        
        uploaded_file = st.file_uploader("Choose PDF file", type=['pdf'])
        
        if uploaded_file:
            cv_text = extract_cv_text(uploaded_file)
            
            if cv_text:
                st.success("✅ CV loaded!")
                
                with st.expander("📝 Preview"):
                    st.text(cv_text[:1000] + "...")
                
                if st.button("🧠 Analyze with AI", type="primary", use_container_width=True):
                    spinner_text = "🔷 Mistral AI working..." if st.session_state.use_mistral else "🤖 CV Analyzer Agent working..."
                    with st.spinner(spinner_text):
                        try:
                            # Determine model and API key based on provider
                            if st.session_state.use_mistral:
                                model = st.session_state.mistral_model
                                api_key = st.session_state.mistral_key
                            elif st.session_state.use_huggingface:
                                model = st.session_state.hf_model
                                api_key = st.session_state.hf_token
                            else:
                                model = "gemini-2.5-flash"
                                api_key = st.session_state.api_key
                            
                            analyzer = CVAnalyzerAgent(
                                api_key=api_key,
                                model=model,
                                use_huggingface=st.session_state.use_huggingface,
                                use_mistral=st.session_state.use_mistral
                            )
                            analysis = analyzer.analyze_cv(cv_text)
                            
                            st.session_state.cv_text = cv_text
                            st.session_state.cv_analysis = analysis
                            
                            st.success("✅ Analysis complete!")
                            st.balloons()
                            
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Level", analysis.get('profile_type', 'N/A').upper())
                            col2.metric("Experience", f"{analysis.get('experience_years', 0)} yrs")
                            col3.metric("Role", analysis.get('primary_role', 'N/A'))
                            
                            st.markdown("### 💪 Strengths")
                            for s in analysis.get('strengths', []):
                                st.markdown(f"✓ {s}")
                            
                            if st.button("🚀 Find Jobs", use_container_width=True):
                                st.session_state.page = 'search'
                                st.rerun()
                        except Exception as e:
                            st.error(f"Analysis failed: {e}")

    elif st.session_state.page == 'search':
        st.markdown("# 🚀 Autonomous Job Search")
        st.markdown("---")
        
        if not st.session_state.cv_text:
            st.warning("⚠️ Upload CV first")
            if st.button("📄 Upload CV"):
                st.session_state.page = 'upload'
                st.rerun()
        
        else:
            cv_analysis = st.session_state.cv_analysis
            
            st.markdown("### 🧠 AI Profile Analysis")
            col1, col2, col3 = st.columns(3)
            col1.metric("Profile", cv_analysis.get('profile_type', 'N/A').upper())
            col2.metric("Experience", f"{cv_analysis.get('experience_years', 0)} yrs")
            col3.metric("Role", cv_analysis.get('primary_role', 'N/A'))
            
            st.markdown("---")
            
            # === LOCATION INPUT ===
            st.markdown("### 📍 Location")
            col_loc1, col_loc2 = st.columns([3, 1])
            with col_loc1:
                user_location = st.text_input(
                    "Your city, town, or country",
                    placeholder="e.g. Paris, France / London / Morocco",
                    help="Enter your location to find nearby jobs. Leave empty to search only remote jobs."
                )
            with col_loc2:
                include_remote = st.checkbox("🌐 Include Remote Jobs", value=True)
            
            st.markdown("---")
            
            # === SOURCE SELECTION ===
            st.markdown("### 🔍 Job Sources")
            source_cols = st.columns(5)
            source_checks = {}
            source_info = {
                'LinkedIn': ('🟦', 'Professional network jobs'),
                'Indeed': ('🟪', 'Largest job board'),
                'RemoteOK': ('🟩', 'Remote-only jobs'),
                'Adzuna': ('🟧', 'Job search aggregator'),
                'Google Jobs': ('🟥', 'Google job aggregator')
            }
            
            for i, (source, (emoji, desc)) in enumerate(source_info.items()):
                with source_cols[i]:
                    source_checks[source] = st.checkbox(
                        f"{emoji} {source}", 
                        value=True,
                        help=desc
                    )
            
            selected_sources = [s for s, checked in source_checks.items() if checked]
            
            st.markdown("---")
            
            max_jobs = st.slider("Jobs per source", 3, 15, 5)
            
            if st.button("🚀 START SEARCH", type="primary", use_container_width=True, 
                          disabled=(not selected_sources and not st.session_state.demo_mode)):
                progress = st.progress(0)
                status = st.empty()
                source_log = st.empty()
                source_results = []
                
                def progress_callback(text, pct):
                    status.text(text)
                    progress.progress(min(pct / 100, 1.0))
                    if text.startswith("✅") or text.startswith("⚠️"):
                        source_results.append(text)
                        source_log.markdown("  \n".join(source_results))
                
                try:
                    # Determine model and API key based on provider
                    if st.session_state.use_mistral:
                        model = st.session_state.mistral_model
                        api_key = st.session_state.mistral_key
                    elif st.session_state.use_huggingface:
                        model = st.session_state.hf_model
                        api_key = st.session_state.hf_token
                    else:
                        model = "gemini-2.5-flash"
                        api_key = st.session_state.api_key
                    
                    coordinator = CoordinatorAgent(
                        api_key=api_key,
                        model=model,
                        use_huggingface=st.session_state.use_huggingface,
                        use_mistral=st.session_state.use_mistral
                    )
                    
                    jobs = coordinator.intelligent_job_search(
                        cv_text=st.session_state.cv_text,
                        jobs_per_site=max_jobs,
                        use_demo=st.session_state.demo_mode,
                        user_location=user_location,
                        selected_sources=selected_sources,
                        include_remote=include_remote,
                        progress_callback=progress_callback,
                        cached_cv_analysis=st.session_state.cv_analysis
                    )
                    
                    jobs = deduplicate_jobs(jobs)
                    
                    progress.progress(100)
                    status.text("✅ Complete!")
                    st.session_state.jobs = jobs
                    st.success(f"✅ Found and analyzed {len(jobs)} jobs!")
                    st.balloons()
                    
                    if st.button("📊 View Dashboard", use_container_width=True):
                        st.session_state.page = 'home'
                        st.rerun()
                
                except Exception as e:
                    st.error(f"Search failed: {e}")

    elif st.session_state.page == 'generate':
        st.markdown("# ✍️ Generate Application")
        st.markdown("---")
        
        if not st.session_state.selected_job:
            st.warning("No job selected")
        else:
            job = st.session_state.selected_job
            st.markdown(f"## {job['title']}")
            st.markdown(f"**{job['company']}** | {job['location']}")
            
            if st.button("🚀 Generate Package", type="primary", use_container_width=True):
                progress = st.progress(0)
                status = st.empty()
                
                try:
                    # Use existing Coordinator from session or create new
                    if st.session_state.use_mistral:
                        model = st.session_state.mistral_model
                        api_key = st.session_state.mistral_key
                    elif st.session_state.use_huggingface:
                        model = st.session_state.hf_model
                        api_key = st.session_state.hf_token
                    else:
                        model = "gemini-2.5-flash"
                        api_key = st.session_state.api_key
                        
                    coordinator = CoordinatorAgent(
                        api_key=api_key, 
                        model=model,
                        use_huggingface=st.session_state.use_huggingface,
                        use_mistral=st.session_state.use_mistral
                    )
                    
                    status.text("Working on your application package...")
                    results = coordinator.run_full_pipeline(st.session_state.cv_text, job)
                    
                    st.success("✅ Package ready!")
                    st.balloons()
                    
                    tab1, tab2, tab3 = st.tabs(["📄 CV", "✉️ Cover Letter", "💼 LinkedIn"])
                    
                    with tab1:
                        st.markdown("### Optimized CV")
                        st.markdown(results['optimized_cv'])
                        st.download_button("📥 Download", results['optimized_cv'], f"CV_{job['company']}.txt")
                    
                    with tab2:
                        st.markdown("### Cover Letter")
                        st.markdown(results['cover_letter'])
                        st.download_button("📥 Download", results['cover_letter'], f"Cover_{job['company']}.txt")
                    
                    with tab3:
                        st.markdown("### LinkedIn Message")
                        st.info(results['linkedin_message'])
                
                except Exception as e:
                    st.error(f"Failed: {e}")
