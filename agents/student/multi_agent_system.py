"""
AI Job Scout - Multi-Agent System
==================================================
Complete autonomous agents with WORKING SCRAPERS + Demo Mode
Refactored for AgenticHire

All 7 Agents:
1. CVAnalyzerAgent - Deep CV understanding
2. JobAnalyzerAgent - Extract requirements & structure
3. MatcherAgent - Semantic matching & scoring
4. CVOptimizerAgent - Tailor CV for specific job
5. WriterAgent - Cover letters & messages
6. AIScraperAgent - Smart multi-source scraping
7. CoordinatorAgent - Orchestrates the entire flow
"""

import os
import time
import json
import logging
import requests
import re
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

# --- CONFIGURATION ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import fix matcher
try:
    from .matcher_fix import patch_matcher_agent, patch_job_analyzer
    MATCHER_FIX_AVAILABLE = True
except ImportError:
    MATCHER_FIX_AVAILABLE = False

# Import tools
try:
    from .tools.job_scraper import ImprovedJobScraper
except ImportError:
    # Fallback or local import if running standalone
    try:
        from job_scraper import ImprovedJobScraper
    except ImportError:
        class ImprovedJobScraper:
            def scrape_all_sources(self, *args, **kwargs): return []

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- AGENT BASE CLASS ---

class BaseAgent:
    """Base class for all AI agents - SUPPORTS GEMINI, HUGGINGFACE, OR MISTRAL"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "mistral-small-latest", 
        use_huggingface: bool = False,
        use_mistral: bool = True
    ):
        self.api_key = api_key or os.getenv('MISTRAL_API_KEY') or os.getenv('HUGGINGFACE_TOKEN') or os.getenv('GOOGLE_API_KEY')
        self.model = model
        self.use_huggingface = use_huggingface
        self.use_mistral = use_mistral
        self.name = "Base Agent"
        
        # HuggingFace API URL
        self.hf_api_url = f"https://api-inference.huggingface.co/models/{model}"
        
        # Mistral API URL
        self.mistral_api_url = "https://api.mistral.ai/v1/chat/completions"

    def _call_llm(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call LLM (routes to correct provider)"""
        try:
            if self.use_mistral:
                return self._call_mistral(prompt, system_prompt, max_tokens)
            elif self.use_huggingface:
                return self._call_huggingface(prompt, system_prompt, max_tokens)
            else:
                return self._call_gemini(prompt, system_prompt, max_tokens)
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return "{}"

    def _call_mistral(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call Mistral AI API"""
        if not self.api_key:
            logger.warning("No Mistral API key provided")
            return "{}"
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.mistral_api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def _call_huggingface(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call HuggingFace Inference API - FAST & FREE!"""
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        # Format prompt for instruction-tuned models
        full_prompt = f"<s>[INST] "
        if system_prompt:
            full_prompt += f"<<SYS>>\n{system_prompt}\n<</SYS>>\n\n"
        full_prompt += f"{prompt} [/INST]"
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.5,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(self.hf_api_url, headers=headers, json=payload, timeout=30)
            result = response.json()
            
            if isinstance(result, list) and 'generated_text' in result[0]:
                return result[0]['generated_text']
            elif isinstance(result, dict) and 'error' in result:
                logger.error(f"HuggingFace Error: {result['error']}")
                return "{}"
            return str(result)
            
        except Exception as e:
            logger.error(f"HuggingFace API failed: {e}")
            return "{}"

    def _call_gemini(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call Gemini API with retry logic (ORIGINAL CODE)"""
        # Note: Keeps original logic but adapted for this class structure
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER PROMPT:\n{prompt}"
            
        data = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_tokens}
        }
        
        try:
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=30)
            if response.status_code != 200:
                logger.error(f"Gemini API Error: {response.text}")
                return "{}"
                
            result = response.json()
            if 'candidates' in result and result['candidates']:
                return result['candidates'][0]['content']['parts'][0]['text']
            return "{}"
        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
            return "{}"

    def _parse_json_response(self, text: str) -> Dict:
        """Extract JSON from LLM response - robust for gemini-2.5-flash"""
        if not text:
            return {}
            
        # Clean markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        # Try to find JSON object
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
                
        # Fallback: simple extraction if structure is known
        try:
            return json.loads(text)
        except:
            logger.warning(f"Failed to parse JSON from {self.name}")
            return {}

# --- 1. CV ANALYZER AGENT ---

class CVAnalyzerAgent(BaseAgent):
    """Agent 1: Analyze CV content"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "CV Analyzer"

    def analyze_cv(self, cv_text: str) -> Dict:
        """Analyze CV and extract insights"""
        system_prompt = """You are an expert HR AI. Analyze the CV and return a JSON object with:
        {
            "profile_type": "Junior/Senior/Exec",
            "primary_role": "Main job title",
            "technical_skills": ["skill1", "skill2"],
            "soft_skills": ["skill1", "skill2"],
            "experience_years": int,
            "strengths": ["strength1", "strength2"],
            "recommended_roles": ["role1", "role2"],
            "education_level": "BSc/MSc/PhD/None"
        }
        Output ONLY valid JSON."""
        
        response = self._call_llm(f"Analyze this CV:\n\n{cv_text[:4000]}", system_prompt)
        return self._parse_json_response(response)

# --- 2. JOB ANALYZER AGENT ---

class JobAnalyzerAgent(BaseAgent):
    """Agent 2: Analyze job postings"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Job Analyzer"
        
        # Apply fix if available
        if MATCHER_FIX_AVAILABLE:
            patch_job_analyzer(self)

    def analyze_job(self, job_title: str, job_description: str, company: str = "Unknown") -> Dict:
        """Analyze job posting"""
        # This method might be monkey-patched by MATCHER_FIX
        system_prompt = """You are an expert Recruiter. Analyze this job and return JSON:
        {
            "required_skills": ["skill1", "skill2"],
            "preferred_skills": ["skill1", "skill2"],
            "experience_level": "Junior/Mid/Senior",
            "role_focus": "Frontend/Backend/Fullstack/Data/etc",
            "key_responsibilities": ["task1", "task2"],
            "red_flags": ["flag1"],
            "salary_range": "Unknown or value"
        }"""
        
        prompt = f"Job: {job_title} at {company}\n\nDescription:\n{job_description[:3000]}"
        response = self._call_llm(prompt, system_prompt)
        return self._parse_json_response(response)

# --- 3. MATCHER AGENT ---

class MatcherAgent(BaseAgent):
    """Agent 3: Match CV to jobs"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Matcher"
        
        # Apply fix if available
        if MATCHER_FIX_AVAILABLE:
            patch_matcher_agent(self)

    def calculate_match(self, cv_analysis: Dict, job_analysis: Dict, job_title: str) -> Dict:
        """Calculate match score"""
        # This method might be monkey-patched by MATCHER_FIX
        system_prompt = """Compare the Candidate Profile and Job Requirements.
        Return JSON:
        {
            "overall_match_score": int (0-100),
            "matching_skills": ["skill1", "skill2"],
            "missing_skills": ["skill1", "skill2"],
            "recommendation": "Strong Match/Good Match/Potential/No Match",
            "application_tips": ["tip1", "tip2"],
            "priority": "Must Apply/Consider/Pass"
        }"""
        
        prompt = f"""
        CANDIDATE:
        Skills: {cv_analysis.get('technical_skills', [])}
        Role: {cv_analysis.get('primary_role')}
        Exp: {cv_analysis.get('experience_years')} years
        
        JOB ({job_title}):
        Required: {job_analysis.get('required_skills', [])}
        Level: {job_analysis.get('experience_level')}
        """
        
        response = self._call_llm(prompt, system_prompt)
        return self._parse_json_response(response)

# --- 4. CV OPTIMIZER AGENT ---

class CVOptimizerAgent(BaseAgent):
    """Agent 4: Optimize CV for jobs"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "CV Optimizer"

    def optimize_cv(self, cv_text: str, job_title: str, job_description: str) -> str:
        """Tailor CV for specific job"""
        system_prompt = """You are an expert Resume Writer. 
        Rewrite the candidate's CV summary and highlights to better match the target job.
        Keep facts truthful but emphasize relevant experience.
        Return MARKDOWN format."""
        
        prompt = f"""
        TARGET JOB: {job_title}
        DESCRIPTION: {job_description[:1000]}...
        
        ORIGINAL CV CONTENT:
        {cv_text[:3000]}
        
        Write an optimized version (Summary + Key Skills + Experience highlights only):
        """
        
        return self._call_llm(prompt, system_prompt)

# --- 5. WRITER AGENT ---

class WriterAgent(BaseAgent):
    """Agent 5: Write application materials"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Writer"

    def write_cover_letter(self, cv_analysis: Dict, job_title: str, company: str, job_description: str) -> str:
        """Generate cover letter"""
        system_prompt = "Write a professional, persuasive cover letter. Keep it concise (max 300 words)."
        
        prompt = f"""
        Role: {job_title} at {company}
        Candidate Role: {cv_analysis.get('primary_role')}
        Strengths: {', '.join(cv_analysis.get('strengths', []))}
        
        Job Context:
        {job_description[:1000]}
        
        Write the letter from the candidate's perspective.
        """
        
        return self._call_llm(prompt, system_prompt)

    def write_linkedin_message(self, cv_analysis: Dict, job_title: str, company: str) -> str:
        """Generate LinkedIn connection request"""
        prompt = f"""
        Write a short LinkedIn connection request (max 300 chars) to a recruiter at {company} regarding the {job_title} role.
        Mention I am a {cv_analysis.get('primary_role')}.
        """
        return self._call_llm(prompt)

# --- 6. SCRAPER AGENT (Using Tools) ---

class AIScraperAgent(BaseAgent):
    """Agent 6: Web scraping with CV-aware keyword search"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Scraper"
        self.tool = ImprovedJobScraper()

    def generate_profile_demo_jobs(self, cv_analysis: Dict) -> List[Dict]:
        """Use AI to generate realistic demo jobs matching the user's actual profile"""
        skills = ", ".join(cv_analysis.get("technical_skills", [])[:5])
        role = cv_analysis.get("primary_role", "Developer")
        
        system_prompt = f"""Generate 5 realistic job postings for a {role} with skills: {skills}.
        Return a JSON list of objects with keys: title, company, location, description, url, source.
        Make them sound authentic."""
        
        response = self._call_llm(f"Generate 5 jobs for {role}", system_prompt)
        jobs = self._parse_json_response(response)
        
        if isinstance(jobs, list):
            # Enforce structure
            for j in jobs:
                j['source'] = 'Demo (AI)'
                j['url'] = '#'
            return jobs
        return self.get_generic_demo_jobs()

    def get_generic_demo_jobs(self) -> List[Dict]:
        """Fallback generic demo jobs"""
        return [
            {
                "title": "Senior Python Developer",
                "company": "TechCorp AI",
                "location": "Remote",
                "description": "We are looking for an expert in Python, Django, and AI agents. Nice to have: React experience.",
                "url": "#",
                "source": "Demo"
            },
            {
                "title": "Full Stack Engineer",
                "company": "StartupX",
                "location": "Paris, France",
                "description": "Join our fast-paced team building the future of recruitment. Stack: Next.js, FastAPI, PostgreSQL.",
                "url": "#",
                "source": "Demo"
            }
        ]

# --- 7. COORDINATOR AGENT ---

class CoordinatorAgent(BaseAgent):
    """Agent 7: Coordinate all other agents"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest", use_huggingface: bool = False, use_mistral: bool = True):
        super().__init__(api_key, model, use_huggingface, use_mistral)
        self.name = "Coordinator"
        
        # Initialize sub-agents
        self.cv_agent = CVAnalyzerAgent(api_key, model, use_huggingface, use_mistral)
        self.job_agent = JobAnalyzerAgent(api_key, model, use_huggingface, use_mistral)
        self.matcher = MatcherAgent(api_key, model, use_huggingface, use_mistral)
        self.optimizer = CVOptimizerAgent(api_key, model, use_huggingface, use_mistral)
        self.writer = WriterAgent(api_key, model, use_huggingface, use_mistral)
        self.scraper = AIScraperAgent(api_key, model, use_huggingface, use_mistral)

    def run_full_pipeline(self, cv_text: str, job_data: Dict) -> Dict:
        """Run complete pipeline for one job"""
        # 1. Analyze Job
        job_analysis = self.job_agent.analyze_job(
            job_data['title'],
            job_data['description'],
            job_data['company']
        )
        
        # 2. Optimize CV
        optimized_cv = self.optimizer.optimize_cv(
            cv_text,
            job_data['title'],
            job_data['description']
        )
        
        # 3. Analyze CV (Original) - Assuming we have it, but for purity re-analyze
        cv_analysis = self.cv_agent.analyze_cv(cv_text)
        
        # 4. Write Cover Letter
        cl = self.writer.write_cover_letter(
            cv_analysis,
            job_data['title'],
            job_data['company'],
            job_data['description']
        )
        
        # 5. Write LinkedIn Message
        li_msg = self.writer.write_linkedin_message(
            cv_analysis,
            job_data['title'],
            job_data['company']
        )
        
        return {
            "job_analysis": job_analysis,
            "optimized_cv": optimized_cv,
            "cover_letter": cl,
            "linkedin_message": li_msg
        }

    def intelligent_job_search(self, cv_text: str, jobs_per_site: int = 5, use_demo: bool = False, 
                             user_location: str = "", selected_sources: List[str] = None, 
                             include_remote: bool = True, progress_callback=None, 
                             cached_cv_analysis: Dict = None) -> List[Dict]:
        """Search multiple sites using CV-derived keywords and analyze jobs"""
        
        def update_progress(text, pct):
            if progress_callback:
                progress_callback(text, pct)
        
        logger.info("🚀 Starting Intelligent Job Search...")
        update_progress("🧠 Agent 1: Analyzing CV...", 10)
        
        # 1. Analyze CV
        if cached_cv_analysis:
            cv_analysis = cached_cv_analysis
        else:
            cv_analysis = self.cv_agent.analyze_cv(cv_text)
        
        # 2. Extract Keywords
        keywords = cv_analysis.get('technical_skills', [])[:3]
        role = cv_analysis.get('primary_role')
        if role:
            keywords.insert(0, role)
        
        update_progress(f"🔍 Agent 6: Scraping jobs for {keywords}...", 30)
        
        # 3. Scrape Jobs
        if use_demo:
             update_progress("🎬 Demo Mode: Generating realistic jobs...", 40)
             raw_jobs = self.scraper.generate_profile_demo_jobs(cv_analysis)
        else:
             raw_jobs = self.scraper.tool.scrape_all_sources(keywords, max_jobs=jobs_per_site)

        if not raw_jobs:
            logger.warning("No jobs found")
            return []
            
        update_progress(f"✨ Found {len(raw_jobs)} jobs. Agents 2 & 3: Analyzing & Matching...", 50)
        
        # 4. Match & Analyze each job
        analyzed_jobs = []
        total = len(raw_jobs)
        
        for i, job in enumerate(raw_jobs):
            # Analyze
            job_analysis = self.job_agent.analyze_job(
                job.get('title', ''), 
                job.get('description', ''),
                job.get('company', '')
            )
            
            # Match
            match_result = self.matcher.calculate_match(
                cv_analysis,
                job_analysis,
                job.get('title', '')
            )
            
            # Enrich job object
            job['ai_analysis'] = {
                'job_details': job_analysis,
                'match_result': match_result
            }
            job['ai_match_score'] = match_result.get('overall_match_score', 0)
            job['ai_priority'] = match_result.get('priority', 'Unknown')
            
            analyzed_jobs.append(job)
            update_progress(f"✅ Processed {i+1}/{total}: {job['title']}", 50 + int((i+1)/total * 40))
            
        return analyzed_jobs
